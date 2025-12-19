from flask import Flask,request, render_template

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])

def index():
    name=request.form.get("name","unknown")
    if name!="unknown":
        name=name.title()
    return render_template("index.html",name=name)

if __name__=="__main__":
    app.run(debug=True)
