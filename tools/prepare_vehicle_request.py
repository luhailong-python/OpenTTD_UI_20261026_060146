from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
identities={
'loco-diesel':'One short rounded diesel locomotive, teal body with ivory horizontal side stripe, a clear forward cab and blunt short front nose, black side cooling grille and brass wheel bogies, rear coupling. No steam chimney.',
'loco-electric':'One double-cab electric locomotive, long ivory body with jade waist stripe, two end cabs, two folded brass pantographs on roof, visible black rail bogies. No steam chimney.',
'loco-monorail':'One rounded streamlined monorail power car, broad dark curved front windshield, jade and ivory shell, narrow central guideway undercarriage and rear coupling. Distinct front nose and flat coupled rear.',
'loco-maglev':'One futuristic rounded maglev power car, elongated low swept nose, continuous jade windshield and ivory streamlined shell, enclosed floating underbody skirts with no exposed conventional wheels. Distinct front nose and flat rear coupling.',
'loco-toy':'One hand-painted wooden lacquer toyland locomotive, jade and ivory carved timber body, small pink accent, round wooden wheels, little brass chimney, front round lamp and rear windowed cabin. Fine painted wood, not plastic.',
'wagon-passenger':'One isolated passenger railway carriage, no locomotive or driver nose. Jade curved roof, ivory walls, six dark passenger windows per side, brass details, black wheel bogies, identical coupling at both ends.',
'wagon-box':'One isolated closed box freight railway wagon, no driver cab. Jade timber rectangular cargo box, gently curved ivory roof, large sliding side door with brass latch, double rear cargo doors, black wheel bogies and end couplings.',
'wagon-hopper':'One isolated EMPTY open-top hopper railway wagon, no cab. Jade tapered steel hopper with fully visible dark empty interior, short black chassis, two end couplings, brass rim. No load, coal or cargo inside.',
'wagon-tank':'One isolated railway liquid tank wagon, no cab. Horizontal ivory cylindrical tank, jade end caps, top brass valve hatch and thin side guardrail, black chassis and end couplings.',
'wagon-vent':'One isolated EMPTY ventilated livestock railway wagon, no cab or animals. Rounded jade roof, warm timber slats and visible empty interior, small brass latch, black wheels, couplings at both ends.',
'wagon-flat':'One isolated EMPTY flatbed railway wagon, no cab. Warm timber deck, low jade side stakes and brass tie-down rings, black chassis and two end couplings. Deck completely empty for a separate cargo layer.',
'road-bus':'One medium-length rounded passenger bus, jade lower body, ivory roof and upper body, five side passenger windows, clear front curved windshield with paired headlights and separate flat rear. Four rubber wheels, no roof ornament.',
'road-open':'One small EMPTY open-bed cargo truck, single front jade driver cab and distinct empty warm-timber cargo bed behind it, low jade sideboards, black rubber wheels, brass bumper. No cargo or cover.',
'road-box':'One small closed box cargo truck, distinct jade front driving cab and ivory rectangular rear delivery box, two rear loading doors and brass handles. Black rubber wheels, rounded corners.',
'road-tank':'One short liquid tanker truck, jade front driver cab, ivory horizontal cylindrical tank behind, jade end caps, small top valve hatch and brass fittings. Black rubber wheels.',
'road-flat':'One EMPTY flatbed cargo truck, distinct jade front driver cab, low warm timber deck behind it, low side stakes and brass tie-down loops. Completely empty rear deck, black rubber wheels.',
'ship-cargo':'One small sturdy cargo ship, pointed raised bow, stern jade-roofed wheelhouse and an EMPTY central open cargo hold, ivory and warm timber hull, brass railings. No sail, no water or wake.',
'ship-tanker':'One short broad liquid tanker ship, pointed bow and stern jade wheelhouse, ivory rounded hull, three circular tank caps with neat pipes on deck, brass guardrail. No sail, no water or wake.',
'ship-ferry':'One two-deck passenger ferry, pointed ivory bow, jade lower hull, rows of dark observation windows, small stern funnel and sheltered rear deck. Clear front versus rear. No water or wake.',
'ship-hovercraft':'One passenger hovercraft, broad dark teal flexible air-cushion skirt, ivory windowed passenger cabin, jade roof, two circular rear propulsion fans. Clear rounded front and fans at rear. No water or wake.',
'air-small-prop':'One small civilian high-wing single-engine propeller airplane, ivory fuselage with jade tail, rounded front nose with stationary dark two-blade propeller, conventional straight main wing and tailplane. No landing strip or shadow.',
'air-large-prop':'One medium civilian twin-engine propeller airplane, ivory fuselage and jade tail, two distinct wing-mounted nacelles with stationary propellers, dark passenger windows, conventional main wing and tailplane. No strip or shadow.',
'air-jet-narrow':'One narrow-body twin-engine passenger jet, ivory rounded fuselage with jade tail and thin gold side stripe, two engines under swept wings, obvious front cockpit and rear tailplane. No weapons or trail.',
'air-jet-wide':'One LARGE wide-body four-engine civilian passenger jet, ivory broad rounded fuselage, jade tail, FOUR visible engine nacelles under swept wings, clear front cockpit and tailplane. No weapons or trail.',
'air-supersonic':'One slender civilian supersonic passenger jet, long gently drooped nose, unmistakable broad triangular delta wing, ivory body with jade tail and small warm gold stripe, four engines below rear wing. No weapons or trail.',
'air-helicopter':'One civilian transport helicopter BODY ONLY: rounded ivory cabin, jade upper fuselage, clear front windshield, long thin tail boom with vertical fin, two landing skids, and top rotor mast. Absolutely NO main rotor blades and NO tail rotor blades: these are separate overlays. Clear cabin nose versus tail.'}
family=sys.argv[1]
base='''Use case: production vehicle prop sprites for an isometric transport simulation. Create an ORIGINAL Taoist chibi high-definition hand-painted eight-direction atlas. The first two references are STRICT STYLE references: jade/teal, warm ivory, restrained delicate warm brass-gold edges, softly rounded full forms, careful crisp painterly shading. The third reference is world camera and setting only. The fourth is ONLY a direction/layout guide; never paint its arrows, labels or grid. No photorealism, plastic gloss, pixel art, text or UI frame.
OUTPUT: wide 2:1 atlas desired 2048x1024. Genuine transparent alpha. EXACTLY four columns and two rows of equal square cells. One COMPLETE isolated vehicle per cell, consistently centered with at least 10 percent transparent margin. No ground, road, rail, platform, shadows, background, labels, grid, border, watermark or accessories outside the vehicle.
CAMERA: fixed orthographic camera 30 degrees above ground, same physical size/paint scheme and identity in all eight cells. Turn the actual vehicle around its vertical axis, do not tilt the image plane. Wheels/hull/skids remain upright.
EXACT ORDER left to right: TOP ROW: N (REAR view; nose points UP away from viewer); NE (rear-right; nose points UPPER RIGHT); E (right-facing SIDE profile; nose RIGHT); SE (front-right; nose LOWER RIGHT). BOTTOM ROW: S (FRONT view; nose DOWN toward viewer); SW (front-left; nose LOWER LEFT); W (left-facing SIDE profile; nose LEFT); NW (rear-left; nose UPPER LEFT). Must include true FRONT, BACK and two SIDE profiles, not eight similar diagonal views. Rear views must show rear hardware rather than front headlights/cockpit. Keep consistent features throughout.
SUBJECT: '''
prompt=base+identities[family]
refs=[r'F:\work\image\designs\mail-ui-v1\01-mail-event.png',r'F:\work\image\designs\team-ui-v2\team-ui-v2.png',str(R/'assets/world-viewport.png'),str(R/'records/vehicles/direction-guide.png')]
d=R/'records/vehicles';d.mkdir(parents=True,exist_ok=True)
(d/(family+'.prompt.txt')).write_text(prompt,encoding='utf-8')
request={'family':family,'prompt':prompt,'references':refs,'output_hint':None}
(d/(family+'.request.json')).write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(request,ensure_ascii=False))
