import simplekml

    kml = simplekml.Kml()

kml.save("test.kml")
kml.newpoint(name=f'[DE-{point["postcode"]}] {point["name"]}; {point["address"]} [{point["city"]}]>[{point["telephone"]}]', coords=[(point["lng"], point["lat"])])
