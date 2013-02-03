function editDemo(demoid, id, loading){
    $.get('demos/edit/'+demoid, function(data) {
      $(id).html(data);
      $(loading).hide();
    });
}