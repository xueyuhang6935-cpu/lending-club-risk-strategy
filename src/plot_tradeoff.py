"""Plot the four existing retention scenarios; no fit or new evaluation."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics',type=Path,default=ROOT/'results/reference/scenario_metrics.csv')
    parser.add_argument('--output',type=Path,default=ROOT/'figures/retention-chargeoff.png')
    args=parser.parse_args();data=pd.read_csv(args.metrics)
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),sharey=True)
    for ax,year in zip(axes,[2014,2015,2016]):
        for name,color in [('S0','#697586'),('S1','#006d77')]:
            part=data.loc[data.evaluation_year.eq(year)&data.strategy.eq(name)].sort_values('actual_retained_ratio')
            ax.plot(part.actual_retained_ratio*100,part.retained_chargeoff_ratio*100,marker='o',label=name,color=color,linewidth=2)
        ax.axvline(80,color='#aab2bd',linestyle='--',linewidth=1)
        ax.set(title=str(year)+(' (already seen)' if year==2016 else ' (development)'),xlabel='Loans retained (%)',xticks=[60,70,80,90])
        ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Charged-off share of retained loans (%)');axes[-1].legend(frameon=False)
    fig.suptitle('Equal-volume selection: credit score (S0) vs four-field logistic (S1)',fontsize=12)
    fig.tight_layout();args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=180);plt.close(fig)
if __name__=='__main__':main()
