(function () {
  var $ = window.$
  var unitsSpan = $('[data-unit="units"]')
  var selectElement = $('[data-unit="select"]')

  selectElement.on('change', function (event) {
    if (event.target.selectedIndex === 0) {
      unitsSpan.html('mK')
    } else {
      unitsSpan.html('mJy')
    }
  })
})()
