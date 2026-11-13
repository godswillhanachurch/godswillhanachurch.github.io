/* 홈 '이번 주 교회': events.json에서 오늘부터 7일 일정을 뽑아 보여 줍니다 */
(function(){
  var box=document.getElementById('homeWeek'); if(!box) return;
  var DAY=['주일','월','화','수','목','금','토'];
  var SUN=[{time:'11:45',title:'주일예배',kind:'worship'},{time:'14:30',title:'목장모임',kind:'group'}];
  function key(d){return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')}
  function parse(s){var p=s.split('-');return new Date(+p[0],+p[1]-1,+p[2])}
  function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  fetch('events.json?v='+Date.now()).then(function(r){return r.json()}).then(function(data){
    var t=new Date(); t.setHours(0,0,0,0); var rows=[];
    for(var i=0;i<7;i++){
      var d=new Date(t); d.setDate(t.getDate()+i); var k=key(d), list=[], rep=[], skip=(data.skip||[]).indexOf(k)>-1;
      (data.events||[]).forEach(function(e){var a=parse(e.date),b=e.end?parse(e.end):a; if(d>=a&&d<=b){ if(e.replace)rep.push(e.replace); list.push({time:e.time||'',title:e.title,note:e.note||'',kind:e.kind||'special'}); }});
      if(!skip){
        (data.weekly||[]).forEach(function(w){ if(d.getDay()===w.day&&rep.indexOf(w.title)<0) list.push({time:w.time||'',title:w.title,note:w.note||'',kind:w.kind||''}); });
        if(d.getDay()===0) SUN.forEach(function(x){ if(rep.indexOf(x.title)<0) list.push(x); });
      }
      list.sort(function(x,y){return (x.time||'99')<(y.time||'99')?-1:1});
      if(list.length) rows.push({d:d,list:list,today:i===0});
    }
    if(!rows.length){box.innerHTML='<li class="hw-none">이번 주 등록된 일정이 없습니다.</li>';return}
    box.innerHTML=rows.slice(0,4).map(function(r){
      return '<li class="hw-day'+(r.today?' is-today':'')+'"><p class="hw-date"><b>'+DAY[r.d.getDay()]+'</b><span>'+(r.d.getMonth()+1)+'.'+r.d.getDate()+(r.today?' · 오늘':'')+'</span></p><ul>'+
        r.list.map(function(e){return '<li><span class="hw-time">'+(esc(e.time)||'—')+'</span><span class="hw-title">'+esc(e.title.replace(/^탈북민사역 \((.*)\)$/,'$1'))+'</span></li>'}).join('')+'</ul></li>';
    }).join('');
  }).catch(function(){box.innerHTML='<li class="hw-none"><a href="news.html#calendar">교회 일정 보기</a></li>'});
})();
