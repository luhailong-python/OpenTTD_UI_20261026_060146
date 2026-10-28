"""Additional source-specific state contracts, independent of mere PNG existence."""
def extra_checks(item,matched,metas,assets,animations):
 req=item['id'];need=item['neededVariants'];cat=item['category'];out=[]
 def test(name,ok,**e):out.append({'test':name,'passed':bool(ok),**e})
 states=[s for m in metas for s in m.get('states',[]) if isinstance(s,dict)]
 if cat=='terrain' and need.get('slopeCodes') and req!='terrain-fence':
  slopes={a.get('slopeCode') for a in matched if a.get('slopeCode') is not None};expected=set(need['slopeCodes']);test('19legal terrain slope geometries',expected<=slopes,expected=sorted(expected),actual=sorted(slopes))
  if need.get('densityStages') is not None:test('all density stages',set(need['densityStages'])<={a.get('densityStage') for a in matched},actual=sorted({a['densityStage'] for a in matched if 'densityStage'in a}))
  if need.get('sourceRandomVariants'):test('all explicit source random-variant bindings',set(range(need['sourceRandomVariants']))<={a.get('sourceRandomVariant')for a in matched},expected=need['sourceRandomVariants'])
  if need.get('coverageFractions'):test('source density0 is quarter coverage, density3 is full coverage',set(need['coverageFractions'])<={a.get('compositeFraction')for a in matched},expected=need['coverageFractions'])
 if req=='road-oneway-markings':
  offsets={a.get('sourceSpriteOffset')for a in matched};test('all18source one-way/closed sprite slots',set(range(18))<=offsets,actual=len(offsets))
  test('post-foundation19slopes×2axes×3direction restrictions',any(set(need['originalSlopeCodes'])<=set(m.get('inputTerrainSlopeCodes',[]))and m.get('completeVariantCoverage')and m.get('noMarkingWhenDrdZero')for m in metas))
 if req=='animation-industry-machinery':
  kinds={a.get('sourceMachineryType')for a in animations if a.get('binding')}
  test('all8source moving machinery and installed particle types',set(need['types'])<=kinds,expected=need['types'],actual=sorted(k for k in kinds if k))
 if req=='terrain-field' and need.get('fieldStages'):
  actual={(s.get('sourceFieldType'),s.get('slopeCode'))for s in states}
  expected={(stage,slope)for stage in need['fieldStages']for slope in need['slopeCodes']}
  test('all9source field stages×19slope bindings',expected<=actual,expected=len(expected),actual=len(expected&actual))
 if req=='terrain-rocks' and need.get('overlayStates'):
  expected={(state,layout,slope)for state in need['overlayStates']for layout in need['layoutsByState'][state]for slope in need['slopeCodes']}
  actual={(a.get('overlayState'),a.get('layoutVariant'),a.get('slopeCode'))for a in matched if a.get('independentRockOverlay')}
  test('independent stone overlays for all source snow/coast states, dry layouts and19slopes',expected<=actual,expected=len(expected),actual=len(expected&actual))
 if req=='terrain-fence' and need.get('sourceStyleIds'):
  expected=len(need['sourceStyleIds'])*len(need['slopeCodes'])*4
  test('6source farm fences×four edges×19slopes have explicit endpoint-height bindings',any(m.get('explicitBindings')==expected and set(need['slopeCodes'])<=set(m.get('slopeCodes',[]))and len(m.get('edges',[]))==4 for m in metas),expected=expected)
 if cat=='industry' and not req.startswith('animation-'):
  expected={l['id'] for l in need.get('layouts',[])};layouts=[l for m in metas for l in m.get('layouts',[])];actual={l['id']for l in layouts};test('all source industry layout tables retained',expected<=actual,expected=len(expected),actual=len(actual))
  construction=[s for m in metas for s in m.get('constructionStates',[]) if isinstance(s,dict)and 'stage'in s];test('4whole industry construction stages',{0,1,2,3}<={s.get('stage')for s in construction})
 if cat=='airport-tile':
  modules=[x for m in metas for x in m.get('moduleLayers',[])];ids={a['id']for a in assets};test('source airport tile ID and explicit ground/building/occlusion ownership',any(m.get('sourceTileId')==need['sourceTileId']for m in metas)and bool(modules)and all(x.get('artId')in ids and x.get('layer')in ['ground','building','occlusion','foreground','front-fence','rear-fence']for x in modules),moduleCount=len(modules))
 if cat=='airport' and req.startswith('airport-'):
  test('source airport footprint retained',any(m.get('sourceFootprintTiles')==need.get('footprintTiles')for m in metas),expected=need.get('footprintTiles'))
 if cat=='station':
  if need.get('sourceLayouts'):
   expected=need['sourceLayouts'];layouts={s.get('layout')for s in states if s.get('layout') is not None};test('all source station layout roles',len(layouts)>=expected,expected=expected,actual=len(layouts))
  if need.get('directions'):
   directions={s.get('direction')for s in states if s.get('direction')};test('all depot direction bindings',len(directions)>=need['directions'],expected=need['directions'],actual=len(directions))
  if need.get('frontRearLayers'):test('every station/depot state has rear and front ownership',bool(states)and all(s.get('layers',{}).get('front')and s.get('layers',{}).get('rear')for s in states))
 if cat=='bridge':
  axes=set(need['axes']);comb={(s.get('axis'),s.get('deck'))for s in states};test('both axes for rail and road bridge decks',{(a,d)for a in axes for d in ['rail','road']}<=comb)
  pieces=set(need['pieces']);test('all7source piece roles and separate piers',bool(states)and all(pieces<=set(s.get('pieces',{}))and s.get('pier')and all(p.get('layers',{}).get('rear')and p.get('layers',{}).get('front')for p in s.get('pieces',{}).values())for s in states))
  if need.get('railTypes'):test('2axes×4rail technologies have actual guideway bindings',{(axis,typ)for axis in need['axes']for typ in need['railTypes']}<={(s.get('axis'),s.get('railType'))for s in states})
 if cat=='tunnel':
  expected={(d,c)for d in need['directions']for c in need['climates']};actual={(s.get('direction'),s.get('climate'))for s in states};test('all4directions×3climate tunnel states',expected<=actual,expected=len(expected),actual=len(actual))
  test('rear/floor/front/occluder ownership explicit',bool(states)and all({'rear','floor','front','occluder'}<=set(s.get('layers',{}))and (s['layers']['floor']or s.get('floorVisible')is False and s.get('floorHiddenReason'))for s in states))
 if cat=='rail' and need.get('compositionMasks'):
  expected={(m,c)for m in need['compositionMasks']for c in need['climateOverlays']};actual={(a.get('compositionMask'),a.get('climate'))for a in matched};test('63track masks×3climate grounds',expected<=actual,expected=len(expected),actual=len(actual&expected))
  bits={a.get('trackBit')for a in matched if a.get('trackBit') is not None};test('6native track-bit overlays',len(bits)>=6,actual=len(bits))
  slopes={a.get('slopeCode')for a in matched if a.get('slopeCode') is not None};test('4track slope directions',len(slopes)>=4,actual=len(slopes))
  if need.get('pathReservationState'):test('PBS reservation tint is a track-only ownership state',any(m.get('assetState')=='path-reservation-debug-highlight'and m.get('states')for m in metas))
  if need.get('railFenceRoles'):test('source track fence8roles/16positions and all4half-tile water corners',any(m.get('sourceRoles')==8 and m.get('sourcePositions')==16 and set(m.get('halfTileWaterCorners',[]))=={'W','N','E','S'} for m in metas))
 if req=='rail-catenary':
  ids={a['id']for a in matched};test('separate left/right pole and wire modules',all('rail-catenary-'+piece+'-'+side in ids for piece in ['post','wire']for side in ['left','right']))
 if req in ['road-road','road-tram']:
  masks={a.get('connectionMask')for a in matched};test('15road connectivity masks',set(need['connectivityMasks'])<=masks)
  contexts={a.get('surfaceContext')for a in matched};contexts.update(c for m in metas for c in m.get('surfaceContexts',[]));test('4road surface contexts',set(need['surfaceContexts'])<=contexts,expected=need['surfaceContexts'],actual=sorted(c for c in contexts if c))
  slopes={a.get('slopeCode')for a in matched if a.get('slopeCode') not in [None,0]};slopes.update(c for m in metas for c in m.get('slopeCodes',[])if c);test('4road slope directions',len(slopes)>=need['slopeDirections'],expected=need['slopeDirections'],actual=len(slopes))
  expected={(m,c,s)for m in need['connectivityMasks']for c in need['surfaceContexts']for s in [3,6,9,12]};actual={(x.get('connectionMask'),x.get('surfaceContext'),x.get('slopeCode'))for x in states};test('every15mask×4context×4slope combination',expected<=actual,expected=len(expected),actual=len(actual&expected),missing=sorted(expected-actual))
  if need.get('wireSeparate'):test('tram overhead separate art binding',any(m.get('overheadSeparateAssets')or m.get('wireSeparateAssets')for m in metas))
  if need.get('roadsideTypes'):test('source roadside lights/trees masks and suppression contracts',any(set(range(16))<=set(m.get('unionConnectionMasks',[]))and {3,5}<=set(m.get('roadsideValues',[]))and m.get('completeVariantCoverage')for m in metas))
 if req=='road-crossing':
  axes={m.get('axis')for m in metas if m.get('states')};test('2axes×4barrier transition bindings',len(axes)==2 and all({'open','closing','closed','opening'}<=set(m['states'])for m in metas if m.get('states')),actual=len(axes))
 if req=='road-works':test('roadworks warning light clip',any(req in a.get('sourceRequirementIds',[])for a in animations))
 if req=='water-sea':test('actual looping sea keys',any(a['id']=='water-sea'and a.get('loop')and len(a['frames'])>=2 for a in animations))
 if req=='water-aqueduct':
  comb={(s.get('axis'),s.get('piece'))for s in states};test('8aqueduct pieces×2axes',{(a,p)for a in ['X','Y']for p in range(8)}<=comb,actual=len(comb))
 if cat=='object' and req!='object-headquarters':test('object ground/placement ownership explicit',any('groundSeparateSuggested'in m or 'groundSeparate'in m for m in metas))
 if cat=='effect':
  rt=next((m['runtimeRecord']for m in metas if m.get('runtimeRecord')),{});n=need.get('sourceFrameCount');test('effect source ID and frame count retained',rt.get('sourceId')==need.get('sourceEffectId')and (n is None or rt.get('deliveredFrameCount',0)>=n),expected=n,actual=rt.get('deliveredFrameCount'))
  test('effect fixed canvas',len({(a['width'],a['height'])for a in matched})==1)
 if cat=='disaster':
  rt=next((m['runtimeRecord']for m in metas if m.get('runtimeRecord')),{});test('exact original disaster subtype binding',rt.get('sourceId')==need.get('sourceDisasterSubType')and bool(rt.get('sourceEnum')))
  if need.get('rotorFramesRequired'):test('actual rotor phase images',len({a['sha256']for a in matched})>1)
 return out
