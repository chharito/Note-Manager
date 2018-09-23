// Execute when the DOM is fully loaded
$(document).ready(function() {

// ajax request and get json from database
  var city = "Sydney";
  var searchtext = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c'";
  //change city variable dynamically as required
  $.getJSON("https://query.yahooapis.com/v1/public/yql?q=" + searchtext + "&format=json", function(data){
   var a = data.query.results.channel.item.forecast;
   
    for(let i=0; i<a.length; i++){
        $('#weather').append('<li>'+a[i]['day']+','+a[i]['high']+','+ a[i]['text'] +'</li>');
        console.log(a[i]);
//        code: "30"
//date: "20 Sep 2018"
//day: "Thu"
//high: "16"
//low: "7"
//text: "Partly Cloudy"
        
    }
   //$('#weather').html("Temperature in " + city + " is " + data.query.results.channel.item.condition.temp + "°C " + data.query.results.channel.item.condition.text);
  });
        
        document.querySelectorAll(".semester").forEach(function(btn){
    
        btn.onclick = function(){

                $('.list').remove();
               $.getJSON("semester/"+btn.dataset.key, function(result){
                   $.each(result, function(i, field){
                       $('#ul1').append('<li class="list list-group-item">'+field['title']+'</li>');
                   });
               });

            };
        });
    
$('#sidebarCollapse').on('click', function () {
                     $('#sidebar').toggleClass('active');
                 });    
    
    
    
}); // close of ready document


