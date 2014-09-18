var iso2countries = {};
var countries = [];
var counts = [];
var entity = null;

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
    $("input[name='publisher']").autocomplete({
        source : observed_countries, minLength : 0, delay : 0, autoFocus : true,
        close : function() { $(this).blur(); visualize(); return true; }
    });
    $("input[name='article']").autocomplete({
        source : observed_countries, minLength : 0, delay : 0, autoFocus : true,
        close : function() { $(this).blur(); visualize(); return true; }
    });
    $("input[type='text']").bind('focus', function(){
        $(this).val('');
        $(this).autocomplete("search");
    } );


    visualize();
};


function init_page(entity) {
    window.entity = entity;
    countries = COUNTRY_DATA;
    if (entity == 'editor') {
        counts = EDITOR_DATA;
    } else if (entity == 'publisher') {
        counts = PUBLISHER_DATA;
    } else {
        alert("unknown entity: " + entity);
    }
    process_data();
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

function countryName2Iso(name) {
    if (name == 'all') {
        return 'all';
    }
    var country = null;
    for (var i = 0; i < countries.length; i++) {
        if (countries[i].name.trim().toLowerCase() == name.trim().toLowerCase()) {
            country = countries[i];
            break;
        }
    }
    if (!country) {
        alert('no known country with name ' + name);
        return null;
    }
    return country.iso;
}

function visualize() {
    var lang = $("input[name='lang']").val();
    if (!lang) {
        return false;
    }
    var article_name = $("input[name='article']").val();
    if (!article_name) {
        return false;
    }
    var publisher_name = $("input[name='publisher']").val();
    if (!publisher_name) {
        return false;
    }
    var article_iso = countryName2Iso(article_name);
    var publisher_iso = countryName2Iso(publisher_name);
    if (!article_iso || !publisher_iso) {
        return;
    }

    // whether to group results by publisher country (default) or article country
    var by_publisher = (publisher_iso == 'all' || article_iso != 'all');

    console.log(article_iso + ', ' + publisher_iso + ', ' + by_publisher);

    var total = 0;
    var filtered = {};

    for (var i = 0; i < counts.length; i++) {
        var row = counts[i];
        var l = row[0];
        var cc1 = row[1];
        var cc1_native = row[2];
        var cc2 = row[3];
        var cc2_native = row[4];
        var kms = row[5];
        var n = row[6];
        if (lang != 'all' && l != lang) {
            continue;
        }
        if (article_iso != 'all' && cc1 != article_iso) {
            continue;
        }
        if (publisher_iso != 'all' && cc2 != publisher_iso) {
            continue;
        }
        var key = (by_publisher ? cc2 : cc1).toUpperCase();
        if (filtered[key]) {
            filtered[key] += n;
        } else {
            filtered[key] = n;
        }
        total += n;
    }

    var label = "";
    if (lang == 'all') {
        label += 'All WP language editions';
    } else {
        label += 'WP-' + lang + ' language edition';
    }

    if (article_iso == 'all') {
        label += ', all geospatial articles';
    } else {
        label += ', articles in ' + article_name;
    }

    if (publisher_iso == 'all') {
        label += ', ' + entity + 's from all countries';
    } else {
        label += ', ' + entity + 's from ' + publisher_name;
    }

    var div = $("div.results:first-of-type");
    div.find("h4").text(label);

    var provenance = {}

    var rows = "";
    var ordered_countries = keys_sorted_by_value(filtered);
    for (var i = 0; i < ordered_countries.length; i++) {
        var c = ordered_countries[i];
        var cn = iso2countries[c.toLowerCase()].name;
        var n = filtered[c];
        provenance[c] = 1.0 * n / total;
        var p = 100.0 * provenance[c];
        var row = "<tr><td>" + cn + "</td><td>" + addCommas(n) + "</td><td>" + p.toFixed(2) + "%</td></tr>";
        rows += row;
    }
    div.find("table.data tbody").html(rows);

    var map_params = {
        backgroundColor: '#666',
        map: 'world_mill_en',
        series: {
            regions: [{
                min: 0.0,
                max: 1.0,
                values: provenance,
                scale: ['#C8EEFF', '#0071A4'],
                normalizeFunction: 'polynomial'
            }]
        },
        onRegionLabelShow   : function(e, el, code){
            var p = (100.0 * filtered[code] / total).toFixed(2);
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
            $("input[name='publisher']").val(iso2countries[iso.toLowerCase()].name);
            $(".jvectormap-label").remove();
            visualize();
        }
    };
    if (article_iso != 'all') {
        map_params.selectedRegions = article_iso.toUpperCase();
    }
    if (publisher_iso!= 'all') {
        map_params.selectedRegions = publisher_iso.toUpperCase();
    }
    var map = $('.world-map:first-of-type').empty().vectorMap(map_params);
    var caption = '';
    if (entity == 'publisher' && by_publisher) {
        caption = '# citations from publishers in country';
    } else if (entity == 'publisher' && !by_publisher) {
        caption = '# citations in articles about country';
    } else if (entity == 'editor' && by_publisher) {
        caption = '# edits by editors in country';
    } else if (entity == 'editor' && !by_publisher) {
        caption = '# edits for articles about country';
    } else {
        console.log("ARGGHHHH!");
    }
    $(".results table.data thead > tr > th:nth-child(2)").html(caption);

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





