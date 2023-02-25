async function get_nearest(lat: number, long: number): Promise<stationdata[]> {
	const station_data = await fetch(
		`https://tankstellenfinder.aral.de/api/v1/locations/nearest_to?lat=${lat}&lng=${long}&autoload=true&travel_mode=driving&avoid_tolls=false&avoid_highways=false&show_stations_on_route=true&corridor_radius=5&format=json`,
	);
	if (station_data.status == 429) {
		console.warn('We are getting rate limited!');
		throw new Error('rate-limit');
	} else {
		return station_data.json();
	}
}

const is_dev: boolean = Deno.args[0] == 'dev';

type stationdata = {
	id: string;
	name: string;
	lat: string;
	lng: string;
	adress: string;
	city: string;
	state: string;
	postcode: string;
	country_code: string;
	telephone: string;
	facilities: string[];
	products: string[];
	opening_hours: string[];
	open_status: string;
	site_brand: string;
	watchlist_id?: string;
	website?: string;
};

let a = 47.2701,
	b = 55.0583,
	c = 5.8655,
	d = 15.0419;

if (is_dev) {
	console.log('using dev mode');
	a = 47.2701, b = 48, c = 5.8655, d = 6.5;
}

async function get_all_stations(): Promise<stationdata[]> {
	let station_data: stationdata[] = [];
	// latitude and longitude are the bounds of germany
	for (let i = a; i < b; i = i + 0.2) {
		for (let x = c; x < d; x = x + 0.2) {
			console.log(`${i}:${x}`);
			let fetching = true;
			let current_station_data: stationdata[] = [];
			while (fetching) {
				try {
					const tmp_station_data: stationdata[] = await get_nearest(i, x);
					fetching = false;
					current_station_data = tmp_station_data;
				} catch (error) {
					console.error(error);
					await new Promise((res) => setTimeout(() => res(''), 120000));
				}
			}
			station_data = [...station_data, ...current_station_data];
		}
	}

	return station_data;
}

const original_station_data: stationdata[] = await get_all_stations();

// filter for country code
const filtered_station_data: stationdata[] = original_station_data.filter((
	station,
) => (station.country_code == 'DE'));

function deduplicate_stations(array: stationdata[]): stationdata[] {
	const uniqueIds = new Set<string>();
	return array.filter((element: stationdata) => {
		if (!uniqueIds.has(element.id)) {
			uniqueIds.add(element.id);
			return element;
		}
	});
}

// remove duplicates
const unique_station_data = deduplicate_stations(filtered_station_data);

console.log(`got ${unique_station_data.length} stations`);

Deno.writeTextFileSync(
	'./out/stations.json',
	JSON.stringify(unique_station_data, undefined, 4),
);
Deno.writeTextFileSync(
	'./out/stations_min.json',
	JSON.stringify(unique_station_data),
);
