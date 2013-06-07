$(document).ready(function(){
    $.ajax({
        dataType: "json",
        url: "http://freegeoip.net/json/",
        success: function(data, status, xhr){
            if (data["country_code"] == "US"){
                var location_suggestion = data["city"] + ", " + data["region_code"];
            } else{
                var location_suggestion = data["city"] + ", " + data["country_name"];
            }
            $("#location-helper").html(location_suggestion);
        }
    });


    $("#time-zone").change(function(event){
        var $target = $(event.target);
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