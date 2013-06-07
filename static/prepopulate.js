$(document).ready(function(){
    $.ajax({
        dataType: "json",
        url: "http://freegeoip.net/json/",
        success: function(data, status, xhr){
            var client_zip = data["zipcode"];
            $("#zipcode-helper").html(client_zip);
        }
    });


    $("#time-zone").change(function(event){
        var $target = $(event.target);
        console.log($target);
        $("#utc-helper").html($target.val());
    });

    // set timezone
    var offset = new Date().getTimezoneOffset() / 60;
    if (offset <= 0){
        var offset_str = "+" + offset;
    } else {
        var offset_str = "-" + offset;
    }
    $("#time-zone").val(offset_str);
    $("#time-zone").change();


    $("#manually-edit-offset").click( function(){
        $("#time-zone").toggleClass("hidden");
        $("#manually-edit-offset").toggleClass("hidden");
        return false;
    })
})