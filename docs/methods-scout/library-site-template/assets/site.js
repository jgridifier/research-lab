// Library site helpers: active nav, copy buttons, KaTeX auto-render, data-driven charts.
(function(){
  var here=(location.pathname.split('/').pop()||'index.html');
  document.querySelectorAll('.nav a').forEach(function(a){
    if((a.getAttribute('href')||'').split('#')[0]===here) a.setAttribute('aria-current','page');
  });
  document.querySelectorAll('pre').forEach(function(p){
    var b=document.createElement('button');b.className='copy';b.type='button';b.textContent='Copy';
    b.onclick=function(){var t=(p.querySelector('code')||p).innerText.replace(/\nCopy$/,'');
      navigator.clipboard&&navigator.clipboard.writeText(t).then(function(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy'},1200)})};
    p.appendChild(b);
  });
  function fmt(v,u){var s=v>=100?v.toFixed(0):v>=10?v.toFixed(1):v>=1?v.toFixed(2):v.toPrecision(3);return s+(u?' '+u:'')}
  // <div class="chart bars" data-unit="s" data-scale="log" data-groups='[{"label":"62 x 14","bars":[["R",98.8],["numba",0.593]]}]'>
  document.querySelectorAll('.chart.bars[data-groups]').forEach(function(el){
    var groups=JSON.parse(el.getAttribute('data-groups')),unit=el.dataset.unit||'',log=el.dataset.scale==='log';
    var all=[].concat.apply([],groups.map(function(g){return g.bars.map(function(b){return b[1]})}));
    var max=Math.max.apply(null,all),min=Math.min.apply(null,all);
    var lo=log?Math.log10(min)-0.3:0,hi=log?Math.log10(max):max;
    var html=el.dataset.title?'<div class="title">'+el.dataset.title+'</div>':'';
    groups.forEach(function(g){
      html+='<div class="group">'+(g.label?'<div class="glabel">'+g.label+'</div>':'');
      g.bars.forEach(function(b,i){
        var v=b[1],w=log?(Math.log10(v)-lo)/(hi-lo):v/hi;w=Math.max(0.02,Math.min(1,w));
        html+='<div class="row"><span class="lab">'+b[0]+'</span><span class="track"><span class="bar c'+(b[2]||Math.min(4,i+1))+'" style="display:block;width:'+(w*100).toFixed(1)+'%"></span></span><span class="val">'+fmt(v,unit)+'</span></div>';
      });
      html+='</div>';
    });
    if(log) html+='<div class="note">Log scale. Shorter is faster.</div>';
    el.insertAdjacentHTML('afterbegin',html);
  });
  // <div class="chart lines" data-x='[0.025,0.05]' data-series='[{"name":"D=14","y":[0.1,0.3]}]' data-ref="0.8" data-xlabel="" data-ylabel="">
  document.querySelectorAll('.chart.lines[data-series]').forEach(function(el){
    var xs=JSON.parse(el.dataset.x),ser=JSON.parse(el.dataset.series),ref=el.dataset.ref?+el.dataset.ref:null;
    var W=640,H=320,L=52,R=16,T=16,B=48,cols=['#3279f9','#2b4fda','#7baaf7','#9aa0a6'];
    var x0=Math.min.apply(null,xs),x1=Math.max.apply(null,xs);
    function X(v){return L+(v-x0)/(x1-x0||1)*(W-L-R)}function Y(v){return T+(1-v)*(H-T-B)}
    var s='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+(el.dataset.title||'chart')+'">';
    [0,0.25,0.5,0.75,1].forEach(function(t){s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(t)+'" y2="'+Y(t)+'" stroke="#e1e6ec"/><text x="'+(L-8)+'" y="'+(Y(t)+4)+'" font-size="12" text-anchor="end" fill="#5f6368">'+t.toFixed(2)+'</text>'});
    xs.forEach(function(v){s+='<text x="'+X(v)+'" y="'+(H-B+20)+'" font-size="12" text-anchor="middle" fill="#5f6368">'+v+'</text>'});
    if(ref!==null) s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(ref)+'" y2="'+Y(ref)+'" stroke="#b3261e" stroke-dasharray="4 4"/><text x="'+(W-R)+'" y="'+(Y(ref)-6)+'" font-size="12" text-anchor="end" fill="#b3261e">'+ref+'</text>';
    ser.forEach(function(se,i){var c=se.color||cols[i%cols.length],d=se.y.map(function(v,j){return (j?'L':'M')+X(xs[j]).toFixed(1)+' '+Y(v).toFixed(1)}).join(' ');
      s+='<path d="'+d+'" fill="none" stroke="'+c+'" stroke-width="2.5"'+(se.dash?' stroke-dasharray="6 4"':'')+'/>';
      se.y.forEach(function(v,j){s+='<circle cx="'+X(xs[j])+'" cy="'+Y(v)+'" r="4" fill="#fff" stroke="'+c+'" stroke-width="2"/>'});});
    if(el.dataset.xlabel) s+='<text x="'+((L+W-R)/2)+'" y="'+(H-8)+'" font-size="13" text-anchor="middle" fill="#3c4043">'+el.dataset.xlabel+'</text>';
    if(el.dataset.ylabel) s+='<text transform="translate(14 '+((T+H-B)/2)+') rotate(-90)" font-size="13" text-anchor="middle" fill="#3c4043">'+el.dataset.ylabel+'</text>';
    s+='</svg><div class="note">'+ser.map(function(se,i){return '<span style="color:'+(se.color||cols[i%cols.length])+'">&#9679;</span> '+se.name}).join(' &nbsp; ')+'</div>';
    el.insertAdjacentHTML('beforeend',(el.dataset.title?'<div class="title">'+el.dataset.title+'</div>':'')+s);
  });
  function math(){if(window.renderMathInElement) renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\(',right:'\\)',display:false}],throwOnError:false})}
  if(document.readyState==='complete') math(); else window.addEventListener('load',math);
})();
// Drop a missing logo quietly (the unfilled template has none).
document.querySelectorAll('.wordmark img').forEach(function(i){function d(){i.remove()}if(i.complete&&!i.naturalWidth)d();else i.addEventListener('error',d)});
