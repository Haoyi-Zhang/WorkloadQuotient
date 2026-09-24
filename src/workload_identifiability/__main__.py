"""CLI for a reproducible, bounded certificate experiment."""
import argparse,json,sys
from pathlib import Path
from .core import produce, BoundExceeded
from .verify import verify,InvalidCertificate,VerificationLimit
from .experiments import campaign,apply_limits

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='command',required=True)
    a=sp.add_parser('reproduce');a.add_argument('--output',type=Path,required=True)
    a=sp.add_parser('graphs');a.add_argument('--output',type=Path,required=True)
    a=sp.add_parser('public');a.add_argument('--output',type=Path,required=True)
    a=sp.add_parser('check');a.add_argument('model',type=Path);a.add_argument('certificate',type=Path)
    a=sp.add_parser('produce');a.add_argument('model',type=Path);a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.command=='reproduce':result=campaign(args.output)
        elif args.command=='graphs':
            from .graph_experiments import campaign as graph_campaign
            result=graph_campaign(args.output)
        elif args.command=='public':
            from .public_experiments import campaign as public_campaign
            result=public_campaign(Path(__file__).resolve().parents[2], args.output)
        else:
            apply_limits();m=json.loads(args.model.read_text())
            if args.command=='check':result=verify(m,json.loads(args.certificate.read_text()))
            else:
                c=produce(m);result=verify(m,c)
                # Exclusive publication: do not overwrite an existing certificate.
                with args.output.open('x',encoding='utf-8') as f:json.dump(c,f,indent=2,sort_keys=True);f.write('\n')
        print(json.dumps({'status':'ACCEPTED','result':result},indent=2,sort_keys=True));return 0
    except (BoundExceeded,VerificationLimit,TimeoutError,MemoryError) as e:
        print(json.dumps({'status':'UNKNOWN','reason':str(e)}));return 2
    except (InvalidCertificate,ValueError,KeyError,IndexError,TypeError,OSError,RecursionError) as e:
        print(json.dumps({'status':'REJECTED','reason':str(e)}));return 1

if __name__=='__main__':sys.exit(main())
