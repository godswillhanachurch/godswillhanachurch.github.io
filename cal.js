// 교회 일정 달력 — events.json을 읽어 월별 달력, 선택한 날의 일정, 다가오는 일정을 보여 줍니다.
// 2026년 11월 이전과 지난 달은 보이지 않고, 오늘 이전 날짜는 흐리게 표시합니다.
(function(){
  var box = document.getElementById('churchCal');
  if (!box || !window.fetch) return;
  var WD = ['일','월','화','수','목','금','토'];
  var today = new Date(); today.setHours(0,0,0,0);
  var FIRST = new Date(2026, 10, 1);                       // 2026년 11월부터 공개
  var thisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  var MIN = thisMonth > FIRST ? thisMonth : FIRST;           // 지난 달로는 넘어가지 않음
  var view = new Date(MIN);
  var sel = today < FIRST ? new Date(FIRST) : new Date(today);
  var data = { weekly: [], monthly: [], events: [], skip: [] };

  function key(d){ return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
  function parse(s){ var p = s.split('-'); return new Date(+p[0], +p[1]-1, +p[2]); }
  function esc(s){ return String(s||'').replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function label(e){ return e.time ? esc(e.time) : (e.kind==='season' ? '절기' : (e.last ? '마감' : (e.range ? '기간' : (e.weekly ? '미정' : '종일')))); }
  // 오늘 진행 중인 신청·기간 일정 (달력 위 안내 띠)
  function ongoing(){
    return (data.events||[]).filter(function(e){ return e.end && parse(e.date) <= today && parse(e.end) >= today; })
      .sort(function(x,y){ return parse(x.end) - parse(y.end); });
  }
  function cls(e){ return (e.special?'is-special':'') + (e.kind==='season'?' is-season':''); }

  function on(d){
    var k = key(d), list = [], replaced = [], skip = (data.skip||[]).indexOf(k) > -1;
    (data.events||[]).forEach(function(e){
      var a = parse(e.date), b = e.end ? parse(e.end) : a;
      if (d >= a && d <= b) {
        if (e.replace) replaced.push(e.replace);
        list.push({ time: e.time||'', title: e.title, note: e.note||'', kind: e.kind||'special', range: !!e.end, last: !!e.end && +d === +b, special: !e.replace && (e.kind||'special') === 'special' });
      }
    });
    if (!skip) {
      (data.monthly||[]).forEach(function(m){
        if (d.getDay() === m.day && Math.ceil(d.getDate()/7) === m.nth) list.push({ time: m.time||'', title: m.title, note: m.note||'', kind: m.kind||'special', special: true });
      });
      (data.weekly||[]).forEach(function(w){
        if (d.getDay() === w.day && replaced.indexOf(w.title) < 0) list.push({ time: w.time||'', title: w.title, note: w.note||'', kind: w.kind||'', weekly: true });
      });
    }
    list.sort(function(x,y){ var a = x.kind==='season'?'':(x.time||'00:00'), b = y.kind==='season'?'':(y.time||'00:00'); return a < b ? -1 : a > b ? 1 : 0; });
    return list;
  }

  // 오늘부터 다가오는 특별 일정·절기·변경 일정 (매주 반복 일정은 제외)
  function upcoming(n){
    var from = today < FIRST ? FIRST : today;
    return (data.events||[]).map(function(e){
      var a = parse(e.date), b = e.end ? parse(e.end) : a;
      return { e: e, a: a, b: b, show: a < from ? from : a };
    }).filter(function(x){ return x.b >= from && !(x.e.end && x.a <= today); })
      .sort(function(x,y){ return x.show - y.show || ((x.e.time||'') < (y.e.time||'') ? -1 : 1); })
      .slice(0, n);
  }

  function render(){
    var y = view.getFullYear(), m = view.getMonth();
    var first = new Date(y, m, 1), days = new Date(y, m+1, 0).getDate();
    var atMin = +view <= +MIN;
    var h = ongoing().map(function(e){
      var b = parse(e.end), left = Math.round((b - today) / 864e5);
      return '<p class="cal-band"><span class="cal-band-tag">'+(/신청/.test(e.title)?'신청 중':'진행 중')+'</span>'
        + '<b>'+esc(e.title)+'</b><span class="cal-band-when">'+(b.getMonth()+1)+'월 '+b.getDate()+'일까지 <em>'+(left===0?'오늘 마감':'D-'+left)+'</em></span>'
        + (e.note?'<small>'+esc(e.note)+'</small>':'')+'</p>';
    }).join('');
    h += '<div class="cal-head"><button type="button" class="cal-nav" data-go="-1" aria-label="이전 달"'+(atMin?' disabled':'')+'>‹</button>'
      + '<strong class="cal-month">'+y+'년 '+(m+1)+'월</strong>'
      + '<button type="button" class="cal-nav" data-go="1" aria-label="다음 달">›</button>'
      + '<button type="button" class="cal-today" data-today>오늘</button></div>';
    h += '<div class="cal-grid" role="grid"><div class="cal-row cal-wd" role="row">'
      + WD.map(function(w,i){ return '<span role="columnheader"'+(i===0?' class="sun"':'')+'>'+w+'</span>'; }).join('') + '</div><div class="cal-row" role="row">';
    for (var i = 0; i < first.getDay(); i++) h += '<span class="cal-empty"></span>';
    for (var d = 1; d <= days; d++){
      var dt = new Date(y, m, d), past = dt < today, ev = past ? [] : on(dt);
      var c = 'cal-day' + (dt.getDay()===0?' sun':'') + (+dt===+today?' today':'') + (+dt===+sel?' sel':'') + (past?' past':'');
      h += '<button type="button" class="'+c+'" data-d="'+key(dt)+'"'+(past?' disabled aria-label="'+(m+1)+'월 '+d+'일 (지난 날)"':' aria-label="'+(m+1)+'월 '+d+'일 일정 '+ev.length+'개"')+(+dt===+sel?' aria-pressed="true"':'')+'>'
        + '<span class="n">'+d+'</span><span class="cal-dots">'
        + ev.filter(function(e){ return !e.range || e.last; }).map(function(e){ return e.special?'special':e.kind; }).filter(function(k,i,a){ return a.indexOf(k)===i; }).slice(0,4).map(function(k){ return '<i class="k-'+k+'"></i>'; }).join('') + '</span></button>';
      if (ev.some(function(e){ return e.last; })) h = h.replace(/<\/button>$/, '<span class="cal-tag">마감</span></button>');
      if ((first.getDay()+d) % 7 === 0 && d < days) h += '</div><div class="cal-row" role="row">';
    }
    h += '</div></div>';

    var list = on(sel);
    h += '<div class="cal-side"><div class="cal-list" aria-live="polite"><p class="cal-sel">'+(+sel===+today?'오늘 · ':'')+(sel.getMonth()+1)+'월 '+sel.getDate()+'일 ('+WD[sel.getDay()]+')</p>';
    h += list.length ? '<ul>'+list.map(function(e){
        return '<li class="'+cls(e)+'"><b>'+label(e)+'</b><span>'+esc(e.title)+(e.note?'<small>'+esc(e.note)+'</small>':'')+'</span></li>';
      }).join('')+'</ul>' : '<p class="cal-none">예정된 일정이 없습니다.</p>';
    h += '</div>';

    var up = upcoming(3);
    if (up.length) {
      h += '<div class="cal-up"><p class="cal-sel">다가오는 일정</p><ul>' + up.map(function(x){
        var e = x.e, ds = x.a < x.show ? '~'+(x.b.getMonth()+1)+'.'+x.b.getDate() : (x.a.getMonth()+1)+'.'+x.a.getDate()+' ('+WD[x.a.getDay()]+')';
        var item = { kind: e.kind||'special', special: !e.replace && (e.kind||'special') === 'special' };
        return '<li class="'+cls(item)+'"><button type="button" class="cal-up-btn" data-jump="'+key(x.show)+'"><b>'+ds+'</b><span>'+esc(e.title)
          + '<small>'+[e.time||'', e.note||''].filter(Boolean).map(esc).join(' · ')+'</small></span></button></li>';
      }).join('') + '</ul></div>';
    }
    h += '</div>';
    box.innerHTML = h;
  }

  box.addEventListener('click', function(e){
    var t = e.target.closest('button'); if (!t || t.disabled) return;
    if (t.dataset.go) {
      var v = new Date(view.getFullYear(), view.getMonth() + (+t.dataset.go), 1);
      if (v < MIN) return;
      view = v; render();
    }
    else if (t.hasAttribute('data-today')) { view = new Date(MIN); sel = today < FIRST ? new Date(FIRST) : new Date(today); render(); }
    else if (t.dataset.jump) { sel = parse(t.dataset.jump); view = new Date(sel.getFullYear(), sel.getMonth(), 1); render(); }
    else if (t.dataset.d) { sel = parse(t.dataset.d); render(); }
  });

  fetch('events.json', { cache: 'no-cache' }).then(function(r){ return r.json(); })
    .then(function(d){ data = d; render(); })
    .catch(function(){ box.innerHTML = '<p class="cal-none">일정을 불러오지 못했습니다. 잠시 후 다시 열어 주세요.</p>'; });
})();
