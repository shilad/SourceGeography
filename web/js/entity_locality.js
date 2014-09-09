var iso2countries = {};
var countries = [];
var counts = [];

function process_data() {
    for (var i = 0; i < countries.length; i++) {
        iso2countries[countries[i].iso] = countries[i];
    }
    console.log('loaded ' + iso2countries.length + ' countries');

    var langs = [];
    var lang_obj = {};

    var observed_countries = [];
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

    langs.sort();
    observed_countries.sort();
    langs.splice(0, 0, 'all');
    observed_countries.splice(0, 0, 'all');

    console.log('loaded ' + langs.length + ' langs');
    console.log('loaded ' + observed_countries.length + ' observed countries');

    $("input[name='lang']").autocomplete({
        source : langs, minLength : 0, delay : 0, autoFocus : true,
        close : function() { $(this).blur(); visualize(); return true; }
    });
    $("input[type='text']").bind('focus', function(){
        $(this).val('');
        $(this).autocomplete("search");
    } );


    visualize();
}


function init_page(entity) {

    $.getJSON( "countries.json",
        function( data ) {
            countries = data;
            if (counts.length > 0) {
                process_data();
            }
        });

    $.getJSON( entity + "-counts.json",
        function( data ) {
            counts = data;
            if (countries.length > 0) {
                process_data();
            }
        });
    $("#go").click(visualize);
}

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

    var total = 0;
    var country_local = {};
    var country_sums = {};
    var filtered = {};

    for (var i = 0; i < counts.length; i++) {
        var row = counts[i];
        var l = row[0];
        var cc1 = row[1].toUpperCase();
        var cc1_native = row[2];
        var cc2 = row[3].toUpperCase();
        var cc2_native = row[4];
        var kms = row[5];
        var n = row[6];
        if (lang != 'all' && l != lang) {
            continue;
        }
        if (!country_sums[cc1]) {
            country_local[cc1] = 0;
            country_sums[cc1] = 0;
        }
        if (cc1 == cc2) {
            country_local[cc1] += n;
        }
        if (filtered[cc2]) {
            filtered[cc2] += n;
        } else {
            filtered[cc2] = n;
        }
        country_sums[cc1] += n;
        total += n;
    }

    var localities = {};
    for (var cc in country_sums) {
        localities[cc] = 1.0 * country_local[cc] / country_sums[cc];
    }

    var label = "Results for ";
    if (lang == 'all') {
        label += 'all WP language editions';
    } else {
        label += 'WP-' + lang + ' language edition';
    }

    var div = $("div.results:first-of-type");
    div.find("h4").text(label);

    var rows = "";
    var ordered_countries = keys_sorted_by_value(localities);
    for (var i = 0; i < ordered_countries.length; i++) {
        var c = ordered_countries[i];
        var cn = iso2countries[c.toLowerCase()].name;
        var n = country_sums[c];
        var p = 100.0 * localities[c];
        var row = "<tr><td>" + cn + "</td><td>" + addCommas(n) + "</td><td>" + p.toFixed(2) + "%</td></tr>";
        rows += row;
    }
    div.find("table.data tbody").html(rows);

    var map_params = {
        backgroundColor: '#666',
        map: 'world_mill_en',
        series: {
            regions: [{
                values: localities,
                scale: ['#C8EEFF', '#0071A4'],
                normalizeFunction: 'polynomial'
            }]
        },
        onRegionLabelShow   : function(e, el, code){
            var p = (100.0 * localities[code]).toFixed(2);
            el.html(el.html()+' ('+p+'%)');
        },
        regionStyle : {
            initial: {
                fill: 'white',
                "fill-opacity": 1,
                stroke: 'none',
                "stroke-width": 0,
                "stroke-opacity": 1
            },
            hover: {
                "fill-opacity": 0.8
            },
            selected: {
                stroke: 'red',
                "stroke-width": 2
            },
            selectedHover: {
            }
        },
        onRegionClick : function(e, iso, isSelected) {
            $("input[name='country']").val(iso2countries[iso.toLowerCase()].name);
            $(".jvectormap-label").remove();
            visualize();
        }
    };
    var map = $('.world-map:first-of-type').empty().vectorMap(map_params);

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





