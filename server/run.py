from app import create_app
from config import * 

args = parse_args()
app = create_app(parse_config(args.config))

def main():
    app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    main()
