'use strict';

function Controller($scope, $http) {
  var debug = false;
  if (debug) {
    $scope.name = 'Arjun Sanyal';
    // todo: add glu mes type, normalcy, context
    // value in mmolPerL
    $scope.glucoses = [
          {'when': '2012-10-23T08:04:11', 'value': 6.5},
          {'when': '2012-10-23T18:04:11', 'value': 7.9},
          {'when': '2012-10-22T08:04:11', 'value': 5.8},
          {'when': '2012-10-22T18:04:11', 'value': 7.0},
          {'when': '2012-10-21T08:04:11', 'value': 5.9},
          {'when': '2012-10-21T18:04:11', 'value': 6.5},
          {'when': '2012-10-20T08:04:11', 'value': 6.8},
          {'when': '2012-10-20T18:04:11', 'value': 5.3},
          {'when': '2012-10-19T08:04:11', 'value': 6.5},
          {'when': '2012-10-19T18:04:11', 'value': 5.2},
          {'when': '2012-10-18T08:04:11', 'value': 7.6},
          {'when': '2012-10-18T18:04:11', 'value': 8.1},
          {'when': '2012-10-17T08:04:11', 'value': 6.5},
          {'when': '2012-10-17T18:04:11', 'value': 5.8},
          {'when': '2012-10-16T08:04:11', 'value': 6.4},
          {'when': '2012-10-16T18:04:11', 'value': 7.9},
        ]
    } else {
      $scope.params = {'wctoken': window.WCTOKEN};
      $scope.name = window.NAME;
      $http.get('/getGlucoseMeasurements', {params: $scope.params})
           .success(function(data) {
             // todo: have a consistent standard for this array or {}}?
             var glucoses = [];
             data.forEach(function(d) {
               glucoses.push({'when': d[0], 'value': d[1]});
             })
             $scope.glucoses = glucoses;
           })
           .error(function(data, status) { alert('error in getGlucoseMeasurements'); })
  }
};
Controller.$inject = ['$scope', '$http'];
