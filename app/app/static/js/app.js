

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
         var url = 'http://localhost:5000/repo_cards?client-key=' + client_key + tags_str;
         $.ajax({
             url: url,
             type: 'GET',
             dataType: 'html',
             success: function(data, status, jqXHR) {
                 $('#repo_cards_container').empty()
                 $('#repo_cards_container').append(data)
             }
        });
    });
}


$(document).ready(
    function() {
        attach_search_event();
    }
);
