// Execute when the DOM is fully loaded
$(document).ready(function() {

// ajax request and get json from database
  var city = "Sydney";
  var searchtext = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c'";
  //change city variable dynamically as required

    $.getJSON("https://query.yahooapis.com/v1/public/yql?q=" + searchtext + "&format=json", function(data){
   var a = data.query.results.channel.item.forecast;
   
    for(let i=0; i<a.length; i++){
        $('#weather').append('<li>'+a[i]['day']+' , Max: '+a[i]['high']+ ', Low: '+a[i]['low']+' , '+ a[i]['text'] +'</li>');
       
//        code: "30"
//date: "20 Sep 2018"
//day: "Thu"
//high: "16"
//low: "7"
//text: "Partly Cloudy"
        
    }
   $('#current_weather').html("Current " + data.query.results.channel.item.condition.temp + "°C " + data.query.results.channel.item.condition.text);
   
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

//calendar 

    $('#datetimepicker1').datepicker({dateFormat: 'dd/mm/yy'});
    
    //assginment note 
    
     
    $('.assign_note').click(function(){
        $('#assign_newid').val($(this).data("assignid"));
        
    });
    
    document.querySelectorAll(".assign_note").forEach(function(btn){
        
        btn.onclick = function(){

                
                $.getJSON("/manage/assignment/note/"+btn.dataset.assignid, function(data){
                    
                    if (data.error == "no data found"){
                        $('#display_note').html("");
                    }else{
                        $('#display_note').html(data.note_title);
                    }
                    
                
                    
                });
            };
        });
    

}); // close of ready document


