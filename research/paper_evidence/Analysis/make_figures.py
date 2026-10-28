"""Publication figures from independently recomputed paper data."""
from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

R=Path(__file__).resolve().parents[1];O=R/'Figures';O.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
def save(fig,name):
    for ext in ['pdf','svg']:fig.savefig(O/(name+'.'+ext),bbox_inches='tight')
    fig.savefig(O/(name+'.png'),dpi=450,bbox_inches='tight')
    plt.close(fig)

fig,ax=plt.subplots(figsize=(7.3,4.35));ax.set_xlim(0,12.3);ax.set_ylim(-.6,6.25);ax.axis('off')
rows=[(4.7,'A  Frozen verdict study','2,000 realizations per model',['Generated request\nwith an authority\nfixture','Candidate\nsemantic contracts','Request anchors\nand policy','Final verdict\n(no writes)'],'#EAF1F8'),
      (2.8,'B  Paired effect study','360 requests per primary model',['Request and\npreferred proposal','Fixed primary and\nindependent\nsecondary','Anchors versus\nfull intersection','Reference SQLite\neffect oracle'],'#EDF5ED'),
      (.9,'C  Native gateway study','48 generated probes per model',['Request and\ntrusted principal','One recorded\nlive extraction','Native contract\nand policy checks','Broker commit\nand retained\nSQLite state'],'#FBF0E8')]
for y,title,n,labels,color in rows:
    ax.text(.05,y+1.15,title,fontsize=10.8,weight='bold');ax.text(12.05,y+1.15,n,ha='right',fontsize=10)
    for i,label in enumerate(labels):
        x=.12+i*3.06
        ax.add_patch(FancyBboxPatch((x,y),2.75,.84,boxstyle='round,pad=.055,rounding_size=.07',facecolor=color,edgecolor='#4D5969',linewidth=.8))
        ax.text(x+1.375,y+.42,label,ha='center',va='center',fontsize=9.8)
        if i<3:ax.add_patch(FancyArrowPatch((x+2.83,y+.42),(x+3.01,y+.42),arrowstyle='-|>',mutation_scale=11,color='#485565'))
ax.text(6.15,-.15,'Native result: three negated requests commit five unauthorized row changes.',ha='center',fontsize=9.8,color='#982E29')
save(fig,'Figure_1_Evaluation_Boundaries')

data=json.loads((R/'Data/Verified_Paper_Results.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(7.2,3.15),gridspec_kw={'width_ratios':[1.25,1]})
stages=['base','anchor_only','clarification_only','full'];labels=['Base verdict','Anchors only','Clarification recovery only','Full reference sequence']
colors={'Qwen3.5-122B':'#246599','GPT-OSS-120B':'#C4712B'}
for model,offset in [('Qwen3.5-122B',-.13),('GPT-OSS-120B',.13)]:
    rows=[next(r for r in data['frozen_stages'] if r['model']==model and r['stage']==s) for s in stages]
    y=[i+offset for i in range(4)];x=[r['accuracy']*100 for r in rows]
    axes[0].errorbar(x,y,xerr=[[r['accuracy']*100-r['group_boot_low']*100 for r in rows],[r['group_boot_high']*100-r['accuracy']*100 for r in rows]],fmt='o',markersize=4.5,capsize=2,color=colors[model],label=model)
    axes[1].plot([r['unsafe_allow'] for r in rows],y,'o',color=colors[model],markersize=4.5)
axes[0].set_yticks(range(4),labels);axes[0].invert_yaxis();axes[0].set_xlim(92,100.7);axes[0].set_xlabel('Exact verdict accuracy (%)');axes[0].grid(axis='x',alpha=.18)
axes[1].set_yticks(range(4),['']*4);axes[1].invert_yaxis();axes[1].set_xlim(-3,89);axes[1].set_xlabel('Unsafe ALLOW verdicts\n(n = 2,000 per model)');axes[1].grid(axis='x',alpha=.18)
axes[0].set_title('A  Verdict correctness',loc='left',fontsize=10);axes[1].set_title('B  Unsafe decisions',loc='left',fontsize=10)
fig.legend(loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.5,-.04));fig.subplots_adjust(left=.31,bottom=.27,wspace=.16)
save(fig,'Figure_2_Frozen_Reference_Ablation')

fig,axes=plt.subplots(1,2,figsize=(7.1,3.5),gridspec_kw={'width_ratios':[1.55,1]})
colors2=['#B9BEC5','#5C87B3','#3E946C','#BB5148'];names=['Output validation error','Accepted, no business change','Authorized completion','Unsafe commit']
values={'Qwen2.5-3B':[35,7,3,3],'Granite-3.3-2B':[43,5,0,0]}
for y,(label,counts) in enumerate(values.items()):
    left=0
    for color,count in zip(colors2,counts):
        axes[0].barh(y,count,left=left,height=.5,color=color,edgecolor='white',linewidth=.8)
        if count:axes[0].text(left+count/2,y,str(count),ha='center',va='center',fontsize=9,color='white' if color in colors2[2:] else '#17212B')
        left+=count
axes[0].set_yticks([0,1],list(values));axes[0].invert_yaxis();axes[0].set_xlim(0,48);axes[0].set_xticks([0,12,24,36,48]);axes[0].set_xlabel('Attempted controlled probes');axes[0].set_title('A  Live native outcomes',loc='left',fontsize=10)
axes[1].barh([0,1,2],[3,0,12],height=.5,color=['#3E946C','#3E946C','#A9CBB8'])
axes[1].set_yticks([0,1,2],['Qwen','Granite','Known-candidate\ncontrol']);axes[1].invert_yaxis();axes[1].set_xlim(0,13);axes[1].set_xticks([0,3,6,9,12]);axes[1].set_xlabel('Complete authorized actions\n(out of 12 expected ALLOW)');axes[1].set_title('B  Positive-action utility',loc='left',fontsize=10)
for y,n in enumerate([3,0,12]):axes[1].text(n+.25,y,str(n),va='center',fontsize=9)
handles=[plt.Rectangle((0,0),1,1,color=c) for c in colors2];fig.legend(handles,names,loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.5,-.08),fontsize=8)
fig.subplots_adjust(left=.19,right=.98,top=.86,bottom=.33,wspace=.74)
save(fig,'Figure_3_Native_Effects_And_Utility')
print('Generated three vector figures plus PNG exports.')
