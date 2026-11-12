document.querySelectorAll('a[href$="#life"]').forEach(function(a){a.addEventListener('click',function(){document.querySelectorAll('.faq-item[open]').forEach(function(d){d.open=false})})});


(function(){
  var v=document.getElementById('bulletinViewer'); if(!v) return;
  var imgs=v.querySelectorAll('.bv-stage img'), tabs=v.querySelectorAll('.bv-tabs button'), last=null, cur=0;
  function show(n){cur=n;imgs.forEach(function(im,k){im.classList.toggle('on',k===n)});tabs.forEach(function(t,k){t.classList.toggle('on',k===n);t.setAttribute('aria-selected',k===n)})}
  // 최근 4주 주보만 보관합니다. 새 주보는 맨 위에 추가하고 가장 오래된 것은 지웁니다.
  var B={
    '447':['2026년 11월 8일','제9권 45호'],
    '446':['2026년 11월 1일','제9권 44호'],
    '445':['2026년 10월 25일','제9권 43호'],
    '444':['2026년 10월 18일','제9권 42호']
  };
  var title=document.getElementById('bvTitle');
  function load(n){var b=B[n]; if(!b) return;
    imgs[0].src='bulletin-'+n+'-1.jpg'; imgs[1].src='bulletin-'+n+'-2.jpg';
    title.innerHTML=b[0]+' 주보 <span>'+b[1]+' (통권 '+n+'호)</span>';}
  function open(e){e.preventDefault();last=document.activeElement;load(this.getAttribute('data-b')||'447');show(0);v.hidden=false;document.body.style.overflow='hidden';document.getElementById('bvClose').focus()}
  function close(){v.hidden=true;document.body.style.overflow='';if(last)last.focus()}
  document.querySelectorAll('.open-bulletin').forEach(function(a){a.addEventListener('click',open)});
  tabs.forEach(function(t,k){t.onclick=function(){show(k)}});
  imgs.forEach(function(im){im.onclick=function(){show((cur+1)%imgs.length)}});
  document.getElementById('bvClose').onclick=close;
  v.addEventListener('click',function(e){if(e.target===v||e.target.classList.contains('bv-stage'))close()});
  document.addEventListener('keydown',function(e){if(v.hidden)return;if(e.key==='Escape')close();if(e.key==='ArrowRight')show(1);if(e.key==='ArrowLeft')show(0)});
})();

(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide')), dots=[].slice.call(document.querySelectorAll('#dots button:not(.pause)'));
  var i=0, timer=null, playing=!matchMedia('(prefers-reduced-motion: reduce)').matches, pause=document.getElementById('pause');
  if(slides.length&&pause){
  function show(n){i=(n+slides.length)%slides.length;slides.forEach(function(s,k){s.classList.toggle('on',k===i)});dots.forEach(function(d,k){d.classList.toggle('on',k===i)})}
  function start(){stop();if(playing)timer=setInterval(function(){show(i+1)},6000)}
  function stop(){if(timer)clearInterval(timer);timer=null}
  document.getElementById('prev').onclick=function(){show(i-1);start()};
  document.getElementById('next').onclick=function(){show(i+1);start()};
  dots.forEach(function(d,k){d.onclick=function(){show(k);start()}});
  function label(){pause.textContent=playing?'❚❚':'▶';pause.setAttribute('aria-label',playing?'자동 넘김 멈춤':'자동 넘김 시작')}
  pause.onclick=function(){playing=!playing;label();start()};
  show(0);label();start();
  }
  var side=document.getElementById('side'), t=document.getElementById('sideToggle');
  t.onclick=function(){var o=side.classList.toggle('open');t.setAttribute('aria-expanded',o);t.textContent=o?'닫기':'메뉴'};
  document.querySelectorAll('.side-nav a').forEach(function(a){a.addEventListener('click',function(){side.classList.remove('open');t.setAttribute('aria-expanded','false');t.textContent='메뉴'})});
})();
document.querySelectorAll('.copy').forEach(function(b){
  b.addEventListener('click',function(){
    var el=document.getElementById(b.dataset.copy), t=el.textContent;
    function done(){var d=document.createElement('div');d.className='toast';d.textContent='계좌번호를 복사했습니다';document.body.appendChild(d);setTimeout(function(){d.remove()},1600)}
    function sel(){var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r)}
    try{navigator.clipboard.writeText(t).then(done,sel)}catch(e){sel()}
  });
});

document.querySelectorAll('.m-tags').forEach(function(ul){
  var box=ul.nextElementSibling;
  ul.addEventListener('click',function(e){
    var b=e.target.closest('.m-tag'); if(!b) return;
    ul.querySelectorAll('.m-tag').forEach(function(x){var on=x===b;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)});
    box.textContent=b.getAttribute('data-d');
  });
});

(function(){
  var side=document.getElementById('side'); if(!side) return;
  var on=false;
  function chk(){var y=on?scrollY>12:scrollY>64; if(y!==on){on=y;side.classList.toggle('shrink',y)}} // 흔들림 방지: 줄어들 때와 커질 때 기준을 다르게
  addEventListener('scroll',chk,{passive:true}); chk();
})();

(function(){
  var v=document.getElementById('albumViewer'); if(!v) return;
  var img=document.getElementById('lbImg'), cap=document.getElementById('lbCap'), cnt=document.getElementById('lbCount'),
      ttl=document.getElementById('lbTitle'), prev=document.getElementById('lbPrev'), next=document.getElementById('lbNext');
  var list=[], cur=0, last=null;
  var vid=document.getElementById('lbVid'), mp4=document.getElementById('lbMp4');
  function stopMedia(){vid.hidden=true; vid.removeAttribute('src'); mp4.pause(); mp4.hidden=true; mp4.removeAttribute('src'); mp4.removeAttribute('poster'); mp4.load();}
  function show(n){cur=n; var p=list[n]; stopMedia(); img.hidden=true;
    if(p.embed){vid.hidden=false; vid.src=p.embed;}
    else if(p.video){mp4.hidden=false; if(p.poster) mp4.poster=p.poster; mp4.src=p.video; mp4.setAttribute('aria-label',p.cap||'영상');}
    else{img.hidden=false; img.src=p.src; img.alt=p.cap||'';} cap.textContent=p.cap||'';
    cnt.textContent=(n+1)+' / '+list.length; prev.disabled=n===0; next.disabled=n===list.length-1;
    prev.hidden=next.hidden=list.length<2;}
  function open(b){try{list=JSON.parse(b.getAttribute('data-photos'))}catch(e){return}
    last=b; ttl.textContent=b.getAttribute('data-title'); var more=v.querySelector('.lb-more'); if(more) more.hidden=b.classList.contains('past-open'); show(0); v.hidden=false; document.body.style.overflow='hidden'; document.getElementById('lbClose').focus();}
  function close(){v.hidden=true; stopMedia(); document.body.style.overflow=''; if(last) last.focus();}
  document.querySelectorAll('.album-card,.past-open').forEach(function(b){b.addEventListener('click',function(){open(b)})});
  prev.onclick=function(){if(cur>0)show(cur-1)}; next.onclick=function(){if(cur<list.length-1)show(cur+1)};
  img.onclick=function(){if(cur<list.length-1)show(cur+1)};
  document.getElementById('lbClose').onclick=close;
  v.addEventListener('click',function(e){if(e.target===v||e.target.classList.contains('lb-stage'))close()});
  document.addEventListener('keydown',function(e){if(v.hidden)return; if(e.key==='Escape')close();
    if(e.key==='ArrowRight'&&cur<list.length-1)show(cur+1); if(e.key==='ArrowLeft'&&cur>0)show(cur-1)});
  var sx=null; v.addEventListener('touchstart',function(e){sx=e.touches[0].clientX},{passive:true});
  v.addEventListener('touchend',function(e){if(sx===null)return; var dx=e.changedTouches[0].clientX-sx; sx=null;
    if(dx<-40&&cur<list.length-1)show(cur+1); if(dx>40&&cur>0)show(cur-1)});
})();

/* 은은한 움직임: 화면에 들어오는 요소를 부드럽게 보여줌 */
(function(){
  if(!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var sel=['.sec-head','.news-head','.latest','.worship-times','.vision-in','.creed','.about-grid > *','.spirit-item',
    '.feature','.news-side','.care-cta','.album-head','.album-grid > li','.mission-col','.ph-strip > *','.reg','.faq-head','.faq-title','.faq-list',
    '.explore-grid > li','#offering .box','.en-box','.en-hero .wrap > *'];
  var els=[].slice.call(document.querySelectorAll(sel.join(',')));
  var vh=innerHeight;
  els.forEach(function(el){
    var parent=el.parentElement, sib=[].slice.call(parent.children).indexOf(el);
    el.classList.add('rv');
    if(/grid|strip/.test(parent.className)) el.classList.add('d'+Math.min(sib,3));
    if(el.getBoundingClientRect().top<vh) el.classList.add('in');   /* 처음 화면에 보이는 건 바로 */
  });
  document.documentElement.classList.add('motion');
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px'});
  els.forEach(function(el){if(!el.classList.contains('in')) io.observe(el)});
})();

// 홈 화면 앱(PWA): 오프라인일 때도 열리도록 서비스 워커 등록
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function(){ navigator.serviceWorker.register('/sw.js').catch(function(){}); });
}

// 방문자 통계(GoatCounter): 바닥글에 누적 방문 수 표시
(function(){
  var el = document.querySelector('[data-visits]');
  if (!el || !window.fetch) return;
  fetch('https://godswillhanachurch.goatcounter.com/counter/TOTAL.json')
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){ if (d && d.count) { el.textContent = d.count; el.closest('.visits').hidden = false; } })
    .catch(function(){});
})();

/* 교회이야기 대표 소식: 배너처럼 넘겨 보기 */
(function(){
  document.querySelectorAll('.fs').forEach(function(box){
    var sl=[].slice.call(box.querySelectorAll('.fs-slide')), dots=[].slice.call(box.querySelectorAll('.fs-dots button')), i=0, t=null;
    if(sl.length<2) return;
    function show(n){i=(n+sl.length)%sl.length; sl.forEach(function(s,k){s.classList.toggle('on',k===i); if(k===i) s.removeAttribute('inert'); else s.setAttribute('inert','')}); dots.forEach(function(d,k){d.classList.toggle('on',k===i); d.setAttribute('aria-current',k===i?'true':'false')})}
    function play(){stop(); if(!matchMedia('(prefers-reduced-motion: reduce)').matches&&!matchMedia('(max-width:900px)').matches) t=setInterval(function(){show(i+1)},7000)}
    function stop(){if(t){clearInterval(t); t=null}}
    box.querySelector('.fs-prev').onclick=function(){show(i-1); play()};
    box.querySelector('.fs-next').onclick=function(){show(i+1); play()};
    dots.forEach(function(d,k){d.onclick=function(){show(k); play()}});
    box.addEventListener('mouseenter',stop); box.addEventListener('mouseleave',play);
    box.addEventListener('focusin',stop);
    var sx=null; box.addEventListener('touchstart',function(e){sx=e.touches[0].clientX},{passive:true});
    box.addEventListener('touchend',function(e){if(sx===null)return; var dx=e.changedTouches[0].clientX-sx; sx=null; if(Math.abs(dx)>40){show(dx<0?i+1:i-1); play()}});
    var h=location.hash&&box.querySelector(location.hash); var start=0; sl.forEach(function(s,k){if(s===h) start=k});
    show(start); play();
  });
})();

/* 홈 1분 메시지 제목을 한 줄로: 칸에 넘치면 글자를 줄입니다 */
(function(){
  var t=document.querySelector('.thumb-short strong'); if(!t) return;
  function fit(){
    t.style.removeProperty('font-size');
    var fs=parseFloat(getComputedStyle(t).fontSize), n=0;
    while(t.scrollWidth>t.clientWidth+1 && fs>11 && n++<40){fs-=.5; t.style.setProperty('font-size',fs+'px','important');}
  }
  fit(); addEventListener('resize',fit);
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(fit);
})();
