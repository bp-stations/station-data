import simplekml

    kml = simplekml.Kml()

kml.save("test.kml")
kml.newpoint(name=f'[DE-{point["postcode"]}] {point["name"]}; {point["address"]} [{point["city"]}]>[{point["telephone"]}]', coords=[(point["lng"], point["lat"])])
kml.newpolygon(name="x",
                       outerboundaryis=[(tmp_ne_2, tmp_sw_1), (tmp_ne_2, tmp_ne_1),
                                        (tmp_sw_2, tmp_ne_1), (tmp_sw_2, tmp_sw_1)],
                       innerboundaryis=[(tmp_ne_2, tmp_sw_1), (tmp_ne_2, tmp_ne_1),
                                        (tmp_sw_2, tmp_ne_1), (tmp_sw_2, tmp_sw_1)])