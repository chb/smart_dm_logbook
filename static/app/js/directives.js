'use strict';

angular.module('App.directives', [])
  .directive('glucoseDay', function() {
    return {
      restrict: 'E',
      terminal: true,
      scope: { val: '=' },
      link: function (scope, element, attrs) {
        // http://bl.ocks.org/3887118
        function getDate(d) { return new Date(d); }
        function getHour(d) {
          var x = new Date(d)
          // dates are in UTC, translate to local time
          return x.getHours() + x.getTimezoneOffset() / 60;
        }

        var margin = {top: 20, right: 20, bottom: 30, left: 40},
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;
        var x = d3.scale.linear().domain([0, 24]).range([0, width]).nice();
        var y = d3.scale.linear().range([height, 0]);
        var color = d3.scale.category10();
        var xAxis = d3.svg.axis().scale(x).orient("bottom");
        var yAxis = d3.svg.axis().scale(y).orient("left");

        var svg = d3.select(element[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // angular listener
        scope.$watch('val', function(newVal, oldVal) {
          if (!newVal) { return; }
          svg.selectAll('*').remove();

          // set the y domain after we have the data to auto scale
          y.domain([0, d3.max(newVal, function(d) { return d.value; })]).nice();

          svg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis)
            .append("text")
              .attr("class", "label")
              .attr("x", width)
              .attr("y", -6)
              .style("text-anchor", "end")
              .text("Time of day");

          svg.append("g")
                  .attr("class", "y axis")
                  .call(yAxis)
                .append("text")
                  .attr("class", "label")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text("Glucose (mmol/L)")

            svg.selectAll(".dot")
                .data(newVal)
              .enter().append("circle")
                .attr("class", "dot")
                .attr("r", 5)
                .attr("cx", function(d) { return x(getHour(d.when)); })
                .attr("cy", function(d) { return y(d.value); })
                .style("fill", function(d) { return color(); });
        });
      }
    }
  })

  .directive('glucoseHistogram', function() {
    return {
      restrict: 'E',
      terminal: true,
      scope: { val: '=' },
      link: function (scope, element, attrs) {
        // http://bl.ocks.org/3885304
        var margin = {top: 20, right: 20, bottom: 30, left: 40},
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        var x_domain = [];
        for (var i = 4; i < 15; i += 1) {
          x_domain.push(i);
          //for (var j = 0; j < 11; j += 1) {
            //x_domain.push(i+j/10);
          //}
        }

        // var x = d3.scale.ordinal().domain(x_domain).rangeRoundBands([0, width], .1);
        var x = d3.scale.quantize().domain(x_domain).range(x_domain);
        var y = d3.scale.linear().range([height, 0]);
        var color = d3.scale.category10();
        var yAxis = d3.svg.axis().scale(y).orient("left");
        // aks hack for xAxis
        var x_scale_hack = d3.scale.linear().range([0, width]);
        var xAxis = d3.svg.axis().scale(x_scale_hack).orient("bottom").tickValues(x_domain);

        var svg = d3.select(element[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // angular listener
        scope.$watch('val', function(newVal, oldVal) {
          if (!newVal) { return; }
          svg.selectAll('*').remove();

          // generate counts
          var counts = [];

          newVal.forEach(function(d) {
            var found = false;
            for (var i = 0; i < counts.length; i += 1) {
              if (counts[i][0] === d.value) {
                counts[i][1] = counts[i][1] + 1;
                found = true;
              }
            }
            if (!found) { counts.push([d.value, 1]); }
          });

          // set the y domain after we have the data to auto scale
          y.domain([0, d3.max(counts, function(d) { return d[1]; })]).nice();

          svg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis)
            .append("text")
              .attr("class", "label")
              .attr("x", width)
              .attr("y", 12)
              .style("text-anchor", "end")
              .text("Glucose (mmol/L)");

          svg.append("g")
                  .attr("class", "y axis")
                  .call(yAxis)
                .append("text")
                  .attr("class", "label")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text("Number of Measurements")

            //counts.forEach(function(d) {
              //console.log(d);
              //console.log(x(d[0])*90-90);
           //});

            svg.selectAll(".bar")
                .data(counts)
              .enter().append("rect")
                .attr("class", "bar")
                .attr("width", 90)
                .attr("x", function(d) { return (x(d[0]) * 90 - 90); })
                .attr("y", function(d) { return y(d[1]); })
                .attr("height", function(d) { return height - y(d[1]); });
        });
      }
    }
  })
