

function attach_search_event() {
     $($('#search_repos')[0]).click(function() {
         var client_key = $.cookie('software-registry-client-key');
         var tags_str = '&';

         var checkboxes = $("input[id^='list-checkbox-']");
         for (i = 0; i < checkboxes.length; i ++) {
             if ($(checkboxes[i]).is(':checked')) {
                 var tag_name = $(checkboxes[i]).parent().siblings("span").text();
                 tags_str += 'tag=' + encodeURIComponent(tag_name) + '&';
             }
         }

         tags_str = tags_str.slice(0, -1);

         var url = 'http://127.0.0.1:5000/api/repos?client-key=' + client_key + tags_str;
         alert(url);
         $.ajax({
             url: url,
             type: 'GET',
             dataType: 'jsonp',
             jsonpCallback: 'processJSONPResponse',
             contentType: "application/json; charset=utf-8",
             complete: function(data, status, jqXHR) {
                 console.log(data);
             },
             error: function(xhr, ajaxOptions, thrownError) {
                 console.log(xhr.responseText);
             }
         });
     });
}


$(document).ready(
    function() { attach_search_event(); }
);
