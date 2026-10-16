"""Vector drawing primitives; copied into each independent project generator."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)

def factorization(out):
    d = Drawing((0, 0, 14.4, 3.5))
    for name, x, label in [
        ('source', 1.8, '$C_p$'+'\n'+r'$\mathbf{h}_p\in p(C_p)$'),
        ('image', 7.2, '$I=f(C_p)$'+'\n'+r'$f(\mathbf{h}_p)=\mathbf{a}$'),
        ('database', 12.6, '$D$'+'\n'+r'$\mathbf{a}\notin q(D)$')]:
        d.box(name, x, 2.55, 3.0, 1.05, label)
    d.edge('source', 'image', 'e', 'w')
    d.edge('image', 'database', 'e', 'w')
    d.text(4.5, 2.95, '$f$ onto image')
    d.text(9.9, 2.95, 'inclusion')
    d.edge('source', 'database', 's', 's',
           via=((1.8, 1.4), (12.6, 1.4)))
    d.text(7.2, 1.65, 'universal homomorphism')
    d.text(7.2, .65, r'$I\models\Sigma$ and $\mathbf{a}\notin q(I)$;  $|I|\leq |D|$')
    d.save(out, 'image-factorization')


def workload(out):
    d = Drawing((0, 0, 13.4, 4.2))
    xs = (1.6, 5.0, 8.4, 11.8)
    for i, x in enumerate(xs):
        d.box(str(i), x, 2.35, 1.6, 1.6,
              str(i)+'\n'+('$p_+$' if i < 2 else '$p_-$'), shape='circle')
        d.arrow((x+.48, 3.0), (x-.48, 3.0), dashed=True,
                via=((x+.62, 3.7), (x-.62, 3.7)))
    for i in range(3):
        d.edge(str(i), str(i+1), 'e', 'w')
    d.edge('3', '0', 's', 's', via=((11.8, 1.05), (1.6, 1.05)))
    d.arrow((3.7, .4), (4.6, .4)); d.text(4.85, .4, 'next', ha='left')
    d.arrow((7.0, .4), (7.9, .4), dashed=True); d.text(8.15, .4, 'clone', ha='left')
    d.save(out, 'workload')


def main():
    parser = argparse.ArgumentParser(description='Render the two proof schematics directly with Python.')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    factorization(args.output)
    workload(args.output)


if __name__ == '__main__':
    main()



