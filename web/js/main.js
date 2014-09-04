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

    $.getJSON( "countries.json",
        function( data ) {
            countries = data;
            if (counts.length > 0) {
                init();
            }
        });

    $.getJSON( "counts.json",
        function( data ) {
            counts = data;
            if (countries.length > 0) {
                init();
            }
        });
    $("#go").click(visualize);
});

/**
 * From http://www.mredkj.com/javascript/numberFormat.html
 * @param nStr
 * @returns {*}
 */
function addCommas(nStr)
{
    nStr += '';
    x = nStr.split('.');
    x1 = x[0];
    x2 = x.length > 1 ? '.' + x[1] : '';
    var rgx = /(\d+)(\d{3})/;
    while (rgx.test(x1)) {
        x1 = x1.replace(rgx, '$1' + ',' + '$2');
    }
    return x1 + x2;
}
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
        var l = row[0];
        var cc1 = row[1];
        var cc2 = row[2].toUpperCase();
        var n = row[3];
        if (lang != 'all' && l != lang) {
            continue;
        }
        if (country_iso != 'all' && cc1 != country_iso) {
            continue;
        }
        if (filtered[cc2]) {
            filtered[cc2] += n;
        } else {
            filtered[cc2] = n;
        }
        total += n;
    }

    console.log(filtered);

    var label = "Results for ";
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
    div.find("h4").text(label);

    var rows = "";
    var ordered_countries = keys_sorted_by_value(filtered);
    for (var i = 0; i < ordered_countries.length; i++) {
        var c = ordered_countries[i];
        var n = filtered[c];
        var p = 100.0 * n / total;
        rows += "<tr><td>" + c + "</td><td>" + addCommas(n) + "</td><td>" + p.toFixed(2) + "%</td></tr>"
    }
    div.find("table.data tbody").html(rows);

    $('.world-map:first-of-type').empty().vectorMap({
        backgroundColor: '#666',
        map: 'world_mill_en',
        series: {
            regions: [{
                values: filtered,
                scale: ['#C8EEFF', '#0071A4'],
                normalizeFunction: 'polynomial'
            }]
        },
        onRegionLabelShow   : function(e, el, code){
            var p = (100.0 * filtered[code] / total).toFixed(2);
            el.html(el.html()+' ('+p+'%)');
        }
    });

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





