function populate_map() {
    var width = 650;
    height = 500;

    var tip = d3.tip()
  .attr('class', 'd3-tip')
  .offset([-5, 0])
  .html(function(d) {
    var dataRow = countryById.get(d.properties.name);
       if (dataRow) {
        //    console.log(dataRow);
           return dataRow.states + ": " + dataRow.mortality;
       } else {
           console.log("no dataRow", d);
           return d.properties.name + ": No data.";
       }
  })

    var svg = d3.select('#uschart2')
    // var svg = d3.select('body')
    //     .append('svg')
    //     .attr('width', width)
    //     .attr('height', height)
        ;

    svg.call(tip);

    var projection = d3.geo.albersUsa()
        .scale(900) // mess with this if you want
        .translate([width / 2, height / 2]);

    var path = d3.geo.path()
        .projection(projection);

    var colorScale = d3.scale.linear().range(["#D4EEFF", "#8B0000"]).interpolate(d3.interpolateLab);

    var countryById = d3.map();

    // $.getJSON($SCRIPT_ROOT + url,{}, function (result) {console.log('data json !!!!!')});
    // <script src="{{ url_for('static', filename='lib/js/dc.js') }}"></script>
    // we use queue because we have 2 data files to load.
    queue()
        .defer(d3.json, 'static/data/USA.json')
        .defer(d3.csv, "static/data/deaths_30days.csv", typeAndSet) // process
        .await(loaded);

    function typeAndSet(d) {
        // d.mortality = +d.mortality;
        d.mortality = parseInt(d.Deaths);
        countryById.set(d.states, d);
        return d;
    }

    function getColor(d) {
        var dataRow = countryById.get(d.properties.name);
        if (dataRow) {
            // console.log(dataRow);
            return colorScale(dataRow.mortality);
        } else {
            // console.log("no dataRow", d);
            return "#ccc";
        }
    }

    function loaded(error, usa, mortality) {

        console.log('Loaded.....................................');

        colorScale.domain(d3.extent(mortality, function(d) {return d.mortality;}));

        var states = topojson.feature(usa, usa.objects.units).features;

        svg.selectAll('path.states')
            .data(states)
            .enter()
            .append('path')
            .attr('class', 'states')
            .attr('d', path)
            .on('mouseover', tip.show)
            .on('mouseout', tip.hide)
            .on('click', function(d){ console.log(d, d.properties.name); dashboard_click(d.properties.name);})
            .attr('fill', function(d,i) {
                return getColor(d);
            })
            .append("title");

        var linear = colorScale;

        svg.append("g")
        .attr("class", "legendLinear")
        .attr("transform", "translate(20,20)");

        var legendLinear = d3.legend.color()
        .shapeWidth(60)
        .orient('horizontal')
        .scale(linear);

        svg.select(".legendLinear")
        .call(legendLinear);

        }
}
