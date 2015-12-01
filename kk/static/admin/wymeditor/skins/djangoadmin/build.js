var stylus = require("stylus");
var fs = require("fs");
var watch = (process.argv.indexOf("-w") > -1);
var busy = false;
function build() {
  if (busy) {
    return;
  }
  busy = true;
  var filename = "skin.styl";
  var styl = fs.readFileSync(filename, "utf8");
  stylus.render(styl, {filename: filename}, function(err, css) {
    if (err) throw err;
    fs.writeFileSync("skin.css", css, "utf8");
    console.log("Compiled " + css.length + " bytes");
    busy = false;
  });
}

build();
if (watch) {
  console.log("Watching for changes");
  setInterval(function() {
    var targetStat = fs.statSync("skin.css");
    var sourceStat = fs.statSync("skin.styl");
    if (+sourceStat.mtime > +targetStat.mtime) {
      build();
    }
  }, 500);
}
