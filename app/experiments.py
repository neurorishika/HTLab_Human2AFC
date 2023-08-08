import numpy as np
import pandas as pd
import os
import hashlib
from datetime import datetime

# load environment variables
from dotenv import load_dotenv

load_dotenv()

class Experiment:

    def __init__(self, 
                 max_trials:int,
                 min_trials:int,
                 naive_trials:int, 
                 db:object,
                 debug:bool=False) -> None:
        """
        Initialize an experiment with a trial and state_info tracker
        """
        self.max_trials = max_trials
        self.min_trials = min_trials
        self.naive_trials = naive_trials
        self.current_trial = 0
        self.state_info = []
        self.responses = []
        self.ready = False
        self.current_points = 0
        self.debug = debug
        self.db = db

    def reset(self)->None:
        """
        Reset the experiment
        """
        self.current_trial = 0
        self.state_info = []
        self.responses = []
        self.ready = False
        self.current_points = 0
    
class MultiLevelMarkov(Experiment):

    def __init__(self,
                 task_id:int,
                 max_trials:int,
                 min_trials:int,
                 naive_trials:int,
                 db:object,
                 debug:bool=False) -> None:
        """
        Setup Turner-Hermundstad MultiLevel Markov experiments
        """
        super().__init__(max_trials, min_trials, naive_trials, db, debug)

        directory = "./data/df_topset_mirror.pkl"

        # create task id
        self.task_id = task_id

        # load using pandas
        try:
            self.taskDB = pd.read_pickle(directory)
        except:
            print('Error loading task database. Please check.')
            return
        
        # find the task in the database
        if self.task_id in self.taskDB.index:
            self.current_task = self.taskDB.loc[self.task_id]['task']
            self.current_state = -1
            self.current_lr = 0 #np.random.choice(2)
            self.ready = True
            self.n_states = len(self.current_task[0])
            self.state_labels = np.array(self.current_task[0], dtype=np.int32)
            self.state_transitions = np.array(self.current_task[1],dtype=np.int32)
        else:
            print('Task not found. Please check.')
            return
    
    def reset(self) -> None:
        """
        Reset the experiment
        """
        super().reset()
        self.current_state = -1
        self.current_lr = 0 #np.random.choice(2)
        self.ready = True
    
    def get_next_trial(self)->(str,int,str,int):
        """
        Get the choices and rewards for the next trial. Returns tuples of (left=A/B, reward_left, right=A/B, reward_right)
        """
        if not self.ready: return
        
        if self.current_trial >= self.max_trials: return (None,None,None,None)

        # print(f"Looking at trial {self.current_trial}.")

        # check if still in naive state
        if self.current_state < 0 and self.current_trial < self.naive_trials-1:
            state_A = -1
            state_B = -1
            reward_A = 0
            reward_B = 0
        elif self.current_state < 0 and self.current_trial == self.naive_trials-1:
            state_A = 0
            state_B = 0
            reward_A = 0
            reward_B = 0
        else:
            # get the next states
            state_A, state_B = self.state_transitions[self.current_state]
            # get the rewards
            reward_A = int(self.state_labels[state_A]*100)
            reward_B = int(self.state_labels[state_B]*100)
        
        if len(self.state_info)==0 or self.state_info[-1]['trial'] != self.current_trial:
            self.state_info.append({
                'trial': self.current_trial,
                'state': self.current_state,
                'state_A': state_A,
                'state_B': state_B,
                'reward_A': reward_A,
                'reward_B': reward_B,
                'lr': self.current_lr
            })

        # if self.current_lr == 0:
        return ('A',reward_A,'B',reward_B)
        # else:
        #     return ('B',reward_B,'A',reward_A)
    
    def update_state(self, response:str)->None:
        """
        Update the state based on the response
        """
        if not self.ready: return

        if self.current_trial < self.naive_trials:
            # print('starting naive trial')
            self.current_state = -1
            return
        elif self.current_trial == self.naive_trials:
            self.current_state = 0
            return
        
        # print('starting normal trial')
        if response == 'A':
            self.current_state = self.state_transitions[self.current_state][0]
        else:
            self.current_state = self.state_transitions[self.current_state][1]

        return
    
    def record_response(self, response:str, reward:int)->None:
        """
        Record the response and reward for the current trial
        """
        if not self.ready: return
        self.responses.append({
            'trial': self.current_trial,
            'response': response,
            'reward': reward,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        # resample the next state
        self.current_lr = 0 #np.random.choice(2)
        self.current_points += reward
        
        print(f"Trial {self.current_trial} completed.")
        self.current_trial += 1

        # update the state
        self.update_state(response)

        return
    
    def write_to_database(self, uniqueID:str)->None:
        """
        Write the data to the database after creating a collection for the uniqueID+'_'+task_id
        """
        # get the number of trials
        n_trials = len(self.responses)
        
        # create a collection for the uniqueID+'_'+task_id
        if n_trials < self.min_trials:
            collection = self.db[uniqueID+'_'+str(self.task_id)+'_incomplete']
        else:
            collection = self.db[uniqueID+'_'+str(self.task_id)]

        print("Writing to collection {}...".format(uniqueID))
        # make sure the number of trials is more than 0, if not, return
        if n_trials == 0:
            print("No trials to write.")
            return "no_trials"
        entries = []
        for i in range(n_trials):
            # print(self.responses[i]['trial'], self.state_info[i]['trial'])
            assert self.responses[i]['trial'] == self.state_info[i]['trial']
            entry = {
                'trial': int(self.responses[i]['trial']),
                'state': int(self.state_info[i]['state']),
                'response': str(self.responses[i]['response']),
                'reward': int(self.responses[i]['reward']),
                'time': str(self.responses[i]['time']),  
            }
            if self.debug:
                entry+={
                    'state_A': int(self.state_info[i]['state_A']), # debug only
                    'state_B': int(self.state_info[i]['state_B']), # debug only
                    'reward_A': int(self.state_info[i]['reward_A']), # debug only
                    'reward_B': int(self.state_info[i]['reward_B']), # debug only
                    'lr': int(self.state_info[i]['lr']), # debug only
                }
            entries.append(entry)
        # write to the database
        collection.insert_many(entries)
        print("Done.")
        if n_trials < self.min_trials:
            print("Not enough trials to get reward.")
            return "not_enough_trials"
        # return the hash of the collection + secret key as confirmation
        hash_object = hashlib.sha256(str.encode(uniqueID+'_'+os.environ.get('SECRET_KEY')))
        return str(hash_object.hexdigest())




        
        

            




        