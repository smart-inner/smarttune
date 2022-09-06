from app import create_app, db
from config import * 

args = parse_args()
app = create_app(parse_config(args.config))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
