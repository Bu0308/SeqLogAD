import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root='/Users/apple/study/DACNTT';
const out=`${root}/outputs/01a0ba15-roadmap-six-phases`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/Bang_ke_hoach_SeqLogAD.xlsx`));
console.log((await wb.inspect({kind:'workbook,sheet,table',maxChars:3500,tableMaxRows:2,tableMaxCols:4})).ndjson);
const preview=await wb.render({sheetName:'Roadmap',range:'A1:I8',scale:1,format:'png'});
await fs.writeFile(`${out}/before.png`,new Uint8Array(await preview.arrayBuffer()));
console.log('READ_ONLY_PREVIEW_DONE');
if(!process.argv.includes('--edit')) process.exit(0);
await fs.copyFile(`${root}/Bang_ke_hoach_SeqLogAD.xlsx`,`${out}/before-migration.xlsx`);
const ids={'P2.2':'P3.1','P2.3':'P3.2','P2.4':'P4.1','P2.5':'P4.2','P2.6':'P4.3','P2.7':'P4.4'};
for(let i=1;i<=8;i++){ids[`P3.${i}`]=`P5.${i}`;ids[`P4.${i}`]=`P6.${i}`;}
const names={'P1':'P1 · Data & Protocol','P2':'P2 · Semantic Expert','P3':'P3 · Sequence Experts','P4':'P4 · Structural Expert & Diversity','P5':'P5 · Adaptation & Fusion','P6':'P6 · Cross-System Validation'};
function mapText(s){
 if(typeof s!=='string'||s.startsWith('='))return s;
 const protectedPaths=[];
 s=s.replace(/(?:[\w.-]+\/)+[^\s;,)]*/g,m=>{protectedPaths.push(m);return `@@PATH${protectedPaths.length-1}@@`;});
 s=s.replace(/P2\.1[–-]P2\.7/g,'@@ALL_EXPERTS@@');
 s=s.replace(/P[234]\.(?:PRE|[1-8])\b/g,m=>ids[m]||m);
 s=s.replace(/P2 · Representation & Experts/g,names.P2).replace(/P3 · Adaptation & Fusion/g,names.P5).replace(/P4 · Cross-System Validation/g,names.P6);
 s=s.replace(/Phase[- ]3\b/g,'Phase 5').replace(/Phase[- ]4\b/g,'Phase 6');
 s=s.replace(/@@ALL_EXPERTS@@/g,'P2.1; P3.1–P3.2; P4.1–P4.4');
 return s.replace(/@@PATH(\d+)@@/g,(_,i)=>protectedPaths[Number(i)]);
}
const sheets=['Executive','Roadmap','Task Register','Gates','Traceability','Research Sources','Task Playbooks'];
const changes=[];
for(const name of sheets){
 if(name==='Research Sources')continue;
 const sh=wb.worksheets.getItem(name), range=sh.getUsedRange(), values=range.values;
 for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
  const old=values[r][c],updated=mapText(old);
  if(old!==updated){sh.getCell(r,c).values=[[updated]];changes.push({sheet:name,row:r+1,column:c+1,before:old,after:updated});}
 }
}
const roadmap=wb.worksheets.getItem('Roadmap');
roadmap.getRange('A9:I10').copyFrom(roadmap.getRange('A7:I8'),'all');
roadmap.getRange('A1').values=[['6-PHASE ROADMAP']];
roadmap.getRange('A2').values=[['Phase 2 complete: Semantic seed 42. Sequence and structural/diversity work continue in Phases 3–4. Original eight-week planning envelope retained.']];
roadmap.getRange('A5:I10').values=[
 [names.P1,'W1–W2','Create multi-source schema, buffer contract and architecture-held-out folds.',8,'Registry, schema, split manifests, leakage audit','G0: Protocol Ready','Source/target leakage','AI + Researcher','Finished'],
 [names.P2,'W3','Freeze base metadata and complete independent Semantic training for BGL, HDFS and Hadoop, seed 42.',2,'P2.PRE prerequisite; P2.1 Semantic adapters and verified final ZIP','Semantic S42 execution complete','Target anomaly performance not yet evaluated','AI + Researcher','Finished'],
 [names.P3,'W3–W4','Train Sequence-LoRA reference and compare a required lighter sequence candidate.',2,'P3.1 reference; P3.2 lighter candidate; sequence controls','Both candidates and controls documented','Long-log encoding and resource cost','AI + Researcher','In progress'],
 [names.P4,'W4','Develop GTAT; validate common evidence, diversity and freeze candidate dispositions.',4,'GTAT, common evidence, diversity diagnostics, freeze package','G2: Expert Diversity Ready','C2 source-label permission unresolved','AI + Researcher','Planned'],
 [names.P5,'W5–W6','Calibrate approved target normal buffer and validate adaptive fusion.',8,'Target memory, drift, uncertainty, fusion and explanations','G1 + G3: Adaptation / Fusion','Gate overfits source domains','AI + Researcher','Planned'],
 [names.P6,'W7–W8','Evaluate held-out targets, robustness and ablations; publish reproducible report.',8,'LOAO results, robustness, reproducibility and report','G4: Final Evaluation','Claims beyond evaluated domains','Researcher + AI','Planned'],
];
roadmap.getRange('A5:I10').format.wrapText=true;
roadmap.getRange('A5:I10').format.rowHeight=66;
roadmap.getRange('A9:I10').format.font={name:'Aptos',size:10,color:'#243746'};
roadmap.getRange('A9:I10').format.verticalAlignment='center';
roadmap.getRange('A9:B9').format.fill='#FFF4DE';
roadmap.getRange('A10:B10').format.fill='#EEEAF6';
roadmap.getRange('A9:B10').format.font.bold=true;
const tasks=wb.worksheets.getItem('Task Register');
for(let r=4;r<36;r++){
 const id=tasks.getCell(r,0).values[0][0];
 tasks.getCell(r,1).values=[[names[id.split('.')[0]]]];
}
tasks.getRange('A2').values=[['32 tasks across 6 phases. P2.PRE is the supporting prerequisite; Phase 2 closes Semantic seed-42 execution.']];
tasks.getRange('K14').values=[['Done']];
tasks.getRange('J14').values=[['P2.PRE PASS; independent Semantic implementation and source-only training complete for BGL/HDFS/Hadoop seed 42; verified final ZIP retained. REP-DG-001 disposition retained. Target anomaly evaluation remains Phase 6.']];
tasks.getRange('C20').values=[['Expert Freeze']];
tasks.getRange('E18').values=[['Validate common evidence across all four candidates: raw score, uncertainty/unknown, coverage, record IDs and lineage. Calibrated score remains null until Phase 5; reject missing provenance.']];
tasks.getRange('E20').values=[['Freeze candidate dispositions, reference artifacts, common interface and reproducibility package. Assemble G2 evidence for researcher review before Phase 5.']];
tasks.getRange('E21').values=[['Receive P4.3 diversity evidence and P4.4 freeze package; verify signed G2 before Phase 5 integration.']];
const executive=wb.worksheets.getItem('Executive');
executive.getRange('H4').values=[['P2 COMPLETE (S42)']];
executive.getRange('H4').format.wrapText=true;
executive.getRange('A4:H4').format.rowHeight=30;
executive.getRange('D10').values=[['BGL/HDFS/Hadoop seed-42 training and final ZIP verified']];
executive.getRange('H10').values=[['Finished']];
executive.getRange('G11:H11').values=[['P3','In progress']];
executive.getRange('G12').values=[['P4']];
executive.getRange('G13').values=[['P5']];
executive.getRange('G14').values=[['P5–P6']];
const trace=wb.worksheets.getItem('Traceability');
const vals=trace.getUsedRange().values;
for(let r=0;r<vals.length;r++)for(let c=0;c<vals[r].length;c++)if(vals[r][c]==='P1–P2')trace.getCell(r,c).values=[['P1–P4']];
const play=wb.worksheets.getItem('Task Playbooks');
for(let r=4;r<36;r++)for(let c=1;c<5;c++){
 let v=play.getCell(r,c).values[0][0];
 if(typeof v==='string')play.getCell(r,c).values=[[v.replace(/Phase[- ]2/g,'expert-development phases').replace(/phase[- ]2/g,'expert-development phases')]];
}
wb.recalculate();
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:20},maxChars:2500})).ndjson);
for(const name of sheets){
 const range=name==='Roadmap'?'A1:I11':name==='Executive'?'A1:H14':name==='Task Register'?'A13:K20':name==='Task Playbooks'?'A13:E20':name==='Research Sources'?'A1:G6':name==='Gates'?'A1:H9':'A1:J9';
 const img=await wb.render({sheetName:name,range,scale:1,format:'png'});
 await fs.writeFile(`${out}/${name.replaceAll(' ','-')}.png`,new Uint8Array(await img.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);
await output.save(`${out}/Bang_ke_hoach_SeqLogAD.xlsx`);
await fs.writeFile(`${out}/cell-changes.json`,JSON.stringify(changes,null,2));
console.log('EXPORTED',out);
