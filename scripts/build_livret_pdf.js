// Builds livret-du-citoyen.html (print-ready) from livret-data.js; PDF via Edge headless (see bottom of run).
const fs=require('fs'),path=require('path');global.window={};
const root=path.join(__dirname,'..');require(path.join(root,'livret-data.js'));const L=window.LIVRET;
const P={"1":"Partie 1 · Principes et valeurs","2":"Partie 2 · Institutions","3":"Partie 3 · Droits et devoirs","4":"Partie 4 · Histoire, géographie, culture","5":"Partie 5 · Vivre en France","A":"Annexes"};
const e=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
let h=`<!doctype html><html lang="fr"><meta charset="utf-8"><title>Livret du Citoyen – Fiches et QCM</title><style>
@page{size:A4;margin:16mm 14mm 20mm;}body{font:11pt/1.4 Segoe UI,Arial,sans-serif;color:#111}
h1{font-size:24pt;margin:0 0 4pt}h2{font-size:16pt;background:#1f3a6e;color:#fff;padding:6pt 10pt;margin:18pt 0 8pt;break-after:avoid}
h3{font-size:12pt;margin:12pt 0 4pt;color:#1f3a6e;break-after:avoid}ul{margin:2pt 0 6pt 18pt;padding:0}li{margin:2pt 0}
.q{break-inside:avoid;border-left:3pt solid #1f3a6e;padding:2pt 0 2pt 8pt;margin:9pt 0}.q b.n{color:#1f3a6e}
.o{margin:1pt 0 1pt 14pt}.ok{color:#0a7a2f;font-weight:700}.ex{font-size:10pt;color:#444;margin-top:3pt}.pg{font-size:9pt;color:#777}
.toc a{color:#1f3a6e}</style><body>
<h1>Livret du Citoyen</h1><div>Édition ${e(L.edition)} · ${L.fiches.length} fiches · ${L.questions.length} questions avec réponses</div>
<p class="pg">Source : Ministère de l'Intérieur – Livret du citoyen. Les bonnes réponses sont en vert (✔).</p>
<h2>Sommaire</h2><ul class="toc">`;
const keys=Object.keys(P);
for(const k of keys)h+=`<li>${P[k]}</li>`;
h+=`</ul><h2 style="break-before:page">I. Fiches de révision</h2>`;
for(const k of keys){const fs_=L.fiches.filter(f=>f[0]===k);if(!fs_.length)continue;
 h+=`<h3 style="font-size:14pt;border-bottom:1pt solid #1f3a6e">${P[k]}</h3>`;
 for(const[,t,pg,pts]of fs_)h+=`<h3>${e(t)} <span class="pg">(livret p. ${pg})</span></h3><ul>${pts.map(x=>`<li>${e(x)}</li>`).join('')}</ul>`}
h+=`<h2 style="break-before:page">II. Questions et réponses</h2>`;let n=0;
for(const k of keys){const qs=L.questions.filter(q=>q[1]===k);if(!qs.length)continue;
 h+=`<h3 style="font-size:14pt;border-bottom:1pt solid #1f3a6e">${P[k]} (${qs.length})</h3>`;
 for(const[,,pg,q,a,w,ex]of qs){n++;h+=`<div class="q"><b class="n">Q${n}.</b> ${e(q)} <span class="pg">(p. ${pg})</span><div class="o ok">✔ ${e(a)}</div>${w.map(x=>`<div class="o">○ ${e(x)}</div>`).join('')}<div class="ex">${e(ex)}</div></div>`}}
fs.writeFileSync(path.join(root,'livret-du-citoyen.html'),h+'</body></html>');console.log('questions',n);
