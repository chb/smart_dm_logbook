'use strict';

function Controller($scope, $http) {
    $scope.params = {
      'person_id': sessionStorage.getItem('person_id'),
      'auth_token': sessionStorage.getItem('auth_token'),
      'shared_secret': sessionStorage.getItem('shared_secret'),
      'selected_record_id': sessionStorage.getItem('selected_record_id'),
    };
    $scope.name = sessionStorage.getItem('name');

    $http.get('/getA1cs', {params: $scope.params})
          .success(function(data) {
            // just one A1c for now
            $scope.A1c = data;
          })
          .error(function(data, status) {
             alert('Error in getA1Cs');
          })

    $http.get('/getGlucoseMeasurements', {params: $scope.params})
          .success(function(data) {
            // todo: have a consistent standard for this array or {}}?
            var glucoses = [];
            data.forEach(function(d) {
              glucoses.push({'when': d[0], 'value': d[1]});
            })
            $scope.glucoses = glucoses;
          })
          .error(function(data, status) {
             alert('Error in getGlucoseMeasurements');
          })

};
Controller.$inject = ['$scope', '$http'];
