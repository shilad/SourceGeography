var countries = [];

function loadCountries(data) {

}


$(function(){
    $('#world-map').vectorMap();

    $("input[name='lang']").autocomplete({ source : ['en', 'fr', 'de', 'uk'], minLength : 0});
    $("input[name='country']").autocomplete({ source : ['United States', 'France'], minLength : 0});
    $("input[type='text']").bind('focus', function(){ $(this).autocomplete("search"); } );

    $.ajax({
        type: "GET",
        url: "countryInfo.txt",
        dataType: "text",
        success: function(data) { loadCountries(data); }
    });
});



