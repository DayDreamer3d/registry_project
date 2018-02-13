

function attach_search_event() {
    $($('#search_repos')[0]).click(function() {
         var client_key = $.cookie('software-registry-client-key');
         var tags_str = '&';

         var checkboxes = $("input[id^='list-checkbox-']");
         if (checkboxes.length == 0) { return null; }
         for (i = 0; i < checkboxes.length; i ++) {
             if ($(checkboxes[i]).is(':checked')) {
                 var tag_name = $(checkboxes[i]).parent().siblings("span").text();
                 tags_str += 'tag=' + encodeURIComponent(tag_name) + '&';
             }
         }

        $('#repo_cards_container').empty();

        if (tags_str.length === 1) { return null; }

         tags_str = tags_str.slice(0, -1);

         var url = 'http://localhost:5000/repo_cards?client-key=' + client_key + tags_str;
         $.ajax({
             url: url,
             type: 'GET',
             dataType: 'html',
             success: function(data, status, jqXHR) {
                 $('#repo_cards_container').append(data);
                 attach_download_event();
             }
        });
    });
}


function attach_download_event() {
    $('.mdl-button').on('click', function() {
        var download_button = $(this);
        var repo_name = $(download_button.parent()[0]).siblings('.mdl-card__title').children().text();

        if (repo_name === '') { return null; }
        var client_key = $.cookie('software-registry-client-key');
        var url = 'http://localhost:5000/api/repos/' + repo_name + '?client-key=' + client_key;

        $.ajax({
            url: url,
            type: 'PUT',
            dataType: 'json',
            success: function(data, status, jqXHR) {
                $(download_button).children('.mdl-badge').attr('data-badge', data.downloads);
            }
       });
    });
}


$(document).ready(
    function() {
        attach_search_event();
    }
);
