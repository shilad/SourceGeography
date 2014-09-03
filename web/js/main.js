var iso2countries = {};
var countries = [];
var counts = [];

function init() {
    for (var i = 0; i < countries.length; i++) {
        iso2countries[countries[i].iso] = countries[i];
    }
    console.log('loaded ' + iso2countries.length + ' countries');

    var langs = ['all'];
    var lang_obj = {};

    var observed_countries = ['all'];
    var country_obj = {};

    for (var i = 0; i < counts.length; i++) {
        var lang = counts[i][0];
        if (!lang_obj[lang]) {
            langs.push(lang);
            lang_obj[lang] = 1;
        }

        var containing_iso = counts[i][1];
        var containing = iso2countries[containing_iso];
        if (containing && !country_obj[containing_iso]) {
            country_obj[containing_iso] = 1;
            observed_countries.push(containing.name);
        }
    }

    console.log('loaded ' + langs.length + ' langs');
    console.log('loaded ' + observed_countries.length + ' observed countries');

    $("input[name='lang']").autocomplete({ source : langs, minLength : 0});
    $("input[name='country']").autocomplete({ source : observed_countries, minLength : 0});
    $("input[type='text']").bind('focus', function(){ $(this).autocomplete("search"); } );

    visualize();
}


$(function(){
    $('.world-map:first-of-type').vectorMap();

    $.getJSON( "countries.json",
        function( data ) {
            countries = data;
            console.log('loaded ' + data.length + ' countries');
            if (counts.length > 0) {
                init();
            }
        });

    $.getJSON( "counts.json",
        function( data ) {
            counts = data;
            console.log('loaded ' + data.length + ' counts');
            if (countries.length > 0) {
                init();
            }
        });
    $("#go").click(visualize);
});

function visualize() {
    var lang = $("input[name='lang']").val();
    if (!lang) {
        alert('no language specified');
        return false;
    }
    var country_name = $("input[name='country']").val();
    if (!country_name) {
        alert('no country specified');
        return false;
    }
    var country_iso;
    if (country_name == 'all') {
        country_iso = 'all'
    } else {
        var country = null;
        for (var i = 0; i < countries.length; i++) {
            if (countries[i].name.trim().toLowerCase() == country_name.trim().toLowerCase()) {
                country = countries[i];
                break;
            }
        }
        if (!country) {
            alert('no known country with name ' + country);
            return false;
        }
        country_iso = country.iso;
    }

    var total = 0;
    var filtered = {};

    for (var i = 0; i < counts.length; i++) {
        var row = counts[i];
        if (lang != 'all' && row[0] != lang) {
            continue;
        }
        if (country_iso != 'all' && row[1] != country_iso) {
            continue;
        }
        if (filtered[row[2]]) {
            filtered[row[2]] += row[3];
        } else {
            filtered[row[2]] = row[3];
        }
        total += row[3];
    }

    console.log('found ' + filtered.length + ' unique matches');

    var label = "Estimated geographic distribution of source publishers for ";
    if (lang == 'all') {
        label += 'all WP language editions';
    } else {
        label += 'WP-' + lang + ' language edition';
    }

    if (country_iso == 'all') {
        label += ', all geospatial articles';
    } else {
        label += ', geospatial articles in ' + country.name;
    }

    var div = $("div.results:first-of-type");
    div.find("h3").text(label);

    var rows = "";
    var countries = keys_sorted_by_value(filtered);
    for (var i = 0; i < countries.length; i++) {
        var c = countries[i];
        var n = filtered[c];
        var p = 100.0 * n / total;
        rows += "<tr><td>" + c + "</td><td>" + n + "</td><td>" + p.toFixed(2) + "%</td></tr>"
    }
    div.find("table.data tbody").html(rows);

    return false;
}

/**
 * From http://stackoverflow.com/questions/5199901/how-to-sort-an-associative-array-by-its-values-in-javascript
 * @param obj
 * @returns {Array}
 */
function keys_sorted_by_value(obj) {
    var tuples = [];

    for (var key in obj) tuples.push([key, obj[key]]);

    tuples.sort(function(a, b) {
        a = a[1];
        b = b[1];

        return a < b ? +1 : (a > b ? -1 : 0);
    });

    var keys = [];
    for (var i = 0; i < tuples.length; i++) {
        keys.push(tuples[i][0]);
    }
    return keys;
}





