$(document).ready(function(){
    $.ajax({
        dataType: "json",
        url: "http://freegeoip.net/json/",
        //data: data,
        success: function(data, status, xhr){
            var client_zip = data["zipcode"];
            $("#zipcode-helper").html(client_zip);
        }
    });

    // set timezone
    var offset = new Date().getTimezoneOffset() / 60;
    if (offset <= 0){
        var offset_str = "+" + offset;
    } else {
        var offset_str = "-" + offset;
    }
    $("#time-zone").val(offset_str);
})