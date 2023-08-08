// Javascript using AJAX to run the 2AFC experiment

// Global variables
var timeout = 500; // time between each update in milliseconds
var debug = false; // set to true to print debug messages to console

// UPDATE LEFT STRING
// this function will get the left string from the server and update the id="left_string" element
// the data is returned as a JSON object with the key "left_string"
function update_left_string() {
    $.ajax({
        type: "GET",
        url: "/get_left_string",
        dataType: "json",
        success: function (data) {
            $("#left_string").html(data.left_string);
            if (debug) {
                console.log("left option: " + data.left_string);
            }
            // check if the left string is 'A' or 'B' and add the appropriate class to the left button
            if (data.left_string == 'A') {
                $("#left_button").addClass("button-A");
                $("#left_button").removeClass("button-B");
            }
            else if (data.left_string == 'B') {
                $("#left_button").addClass("button-B");
                $("#left_button").removeClass("button-A");
            }
        }
    });
}

// UPDATE RIGHT STRING
// this function will get the right string from the server and update the id="right_string" element
// the data is returned as a JSON object with the key "right_string"
function update_right_string() {
    $.ajax({
        type: "GET",
        url: "/get_right_string",
        dataType: "json",
        success: function (data) {
            $("#right_string").html(data.right_string);
            if (debug) {
                console.log("right option: " + data.right_string);
            }
            // check if the right string is 'A' or 'B' and add the appropriate class to the right button
            if (data.right_string == 'A') {
                $("#right_button").addClass("button-A");
                $("#right_button").removeClass("button-B");
            }
            else if (data.right_string == 'B') {
                $("#right_button").addClass("button-B");
                $("#right_button").removeClass("button-A");
            }
        }
    });
}

// UPDATE POINTS AND TRIALS
// this function will get the points,trials and winnings from the server and update the id="points" and id="trials" and id="winnings" elements
// the data is returned as a JSON object with the keys "points" and "trials" and "winnings"
function update_points_and_trial() {
    $.ajax({
        type: "GET",
        url: "/get_points_and_trial",
        dataType: "json",
        success: function (data) {
            $("#points").html(data.points);
            // add 1 to the trial number
            $("#trial").html(data.trial + 1);
            $("#winnings").html(data.winnings);
            if (debug) {
                console.log("points: " + data.points);
                console.log("trial: " + (data.trial + 1));
                console.log("winnings: " + data.winnings);
            }
        }
    });
}

// CALL UPDATE LEFT STRING and UPDATE RIGHT STRING and UPDATE POINTS AND TRIALS on page load
$(document).ready(function () {
    update_left_string();
    update_right_string();
    update_points_and_trial();
    // use AJAX to get if it in debug mode and chenge the value of the global variable debug
    $.ajax({
        type: "GET",
        url: "/is_debug_mode",
        dataType: "json",
        success: function (data) {
            debug = data.debug;
            if (debug) {
                console.log("debug mode: " + debug);
            }
        }
    });
});

// SHOW LEFT REWARD
// this function will get the left reward from the server and update the id="left_string" element
// the data is returned as a JSON object with the key "left_reward"
function show_left_reward() {
    $.ajax({
        type: "GET",
        url: "/get_left_reward",
        dataType: "json",
        success: function (data) {
            $("#left_string").html(data.left_reward);
            $("#right_string").html("");
            if (debug) {
                console.log("left reward: " + data.left_reward);
            }
            // check if the left reward is '0', '100', '200' or '300' and add the appropriate class to the left button
            if (data.left_reward == '0') {
                $("#left_button").addClass("button-none");
                $("#left_button").removeClass("button-low");
                $("#left_button").removeClass("button-med");
                $("#left_button").removeClass("button-high");
            }
            else if (data.left_reward == '100') {
                $("#left_button").addClass("button-low");
                $("#left_button").removeClass("button-none");
                $("#left_button").removeClass("button-med");
                $("#left_button").removeClass("button-high");
            }
            else if (data.left_reward == '200') {
                $("#left_button").addClass("button-med");
                $("#left_button").removeClass("button-none");
                $("#left_button").removeClass("button-low");
                $("#left_button").removeClass("button-high");
            }
            else if (data.left_reward == '300') {
                $("#left_button").addClass("button-high");
                $("#left_button").removeClass("button-none");
                $("#left_button").removeClass("button-low");
                $("#left_button").removeClass("button-med");
            }
        }
    });
}

// SHOW RIGHT REWARD
// this function will get the right reward from the server and update the id="right_string" element
// the data is returned as a JSON object with the key "right_reward"
function show_right_reward() {
    $.ajax({
        type: "GET",
        url: "/get_right_reward",
        dataType: "json",
        success: function (data) {
            $("#right_string").html(data.right_reward);
            $("#left_string").html("");
            if (debug) {
                console.log("right reward: " + data.right_reward);
            }
            // check if the right reward is '0', '100', '200' or '300' and add the appropriate class to the right button
            if (data.right_reward == '0') {
                $("#right_button").addClass("button-none");
                $("#right_button").removeClass("button-low");
                $("#right_button").removeClass("button-med");
                $("#right_button").removeClass("button-high");
            }
            else if (data.right_reward == '100') {
                $("#right_button").addClass("button-low");
                $("#right_button").removeClass("button-none");
                $("#right_button").removeClass("button-med");
                $("#right_button").removeClass("button-high");
            }
            else if (data.right_reward == '200') {
                $("#right_button").addClass("button-med");
                $("#right_button").removeClass("button-none");
                $("#right_button").removeClass("button-low");
                $("#right_button").removeClass("button-high");
            }
            else if (data.right_reward == '300') {
                $("#right_button").addClass("button-high");
                $("#right_button").removeClass("button-none");
                $("#right_button").removeClass("button-low");
                $("#right_button").removeClass("button-med");
            }
        }
    });
}

// LEFT BUTTON CLICK
// On left button click, the following happens:
// 1. The left button is highlighted
// 2. The left reward is shown
// 3. A message is sent to the server that the left button was clicked by calling the /left_response route that returns a JSON object with the key "success"
// 4. The both buttons are disabled for 1 second
// After 1 second, 
// 1. The left button is unhighlighted
// 2. The left string and right string are updated
// 3. The points and trial are updated
// 4. The both buttons are enabled

function left_button_click() {

    // run the show_left_reward function and wait for 500 ms before sending the message to the server
    show_left_reward();
    
    $("#left_button").addClass("button-chosen");

    $("#left_button").addClass("button-disabled");
    $("#right_button").addClass("button-disabled");
    $("#left_button").prop("disabled", true);
    $("#right_button").prop("disabled", true);
    
    
    
    setTimeout(function () {
        $.ajax({
            type: "GET",
            url: "/left_response",
            dataType: "json",
            success: function (data) {
                if (debug) {
                    console.log("Left response: " + data.success);
                }
            }
        });
        
        setTimeout(function () {
            $("#left_button").removeClass("button-chosen");
             
            update_left_string();
            update_right_string();
            update_points_and_trial();

            $("#left_button").prop("disabled", false);
            $("#right_button").prop("disabled", false);
            $("#left_button").removeClass("button-disabled");
            $("#right_button").removeClass("button-disabled");
        }, timeout);
    }, timeout);
    
}

// SAME AS LEFT BUTTON CLICK, BUT FOR RIGHT BUTTON
function right_button_click() {

    // run the show_right_reward function and wait for 500 ms before sending the message to the server
    show_right_reward();

    $("#right_button").addClass("button-chosen");

    $("#left_button").addClass("button-disabled");
    $("#right_button").addClass("button-disabled");
    $("#left_button").prop("disabled", true);
    $("#right_button").prop("disabled", true);


    setTimeout(function () {
        $.ajax({
            type: "GET",
            url: "/right_response",
            dataType: "json",
            success: function (data) {
                if (debug) {
                    console.log("Right response: " + data.success);
                }
            }
        });
        
        setTimeout(function () {
            $("#right_button").removeClass("button-chosen");
            
            update_left_string();
            update_right_string();
            update_points_and_trial();

            $("#left_button").prop("disabled", false);
            $("#right_button").prop("disabled", false);
            $("#left_button").removeClass("button-disabled");
            $("#right_button").removeClass("button-disabled");
        }, timeout);
    }, timeout);
    
}