"""Map all original house tile IDs to documented art families and parent footprints."""
from pathlib import Path
import json,collections
import world_pack as wp
ROOT=wp.ROOT
FAMILIES={
'traditional':['thatched-cottage','courtyard-dwelling','timber-rowhouse','paired-gables','courtyard-mansion','pavilion-apartments','small-temple-chapel','city-temple','townhall'],
'commerce':['food-market','teahouse','post-office','bank','clinic','school','theatre','museum','outdoor-stadium'],
'dense':['residential-block','slender-apartment','corner-hotel','office-block','stepped-offices','shopping-hall','jade-skyscraper','cylindrical-tower','cinema'],
'climates':['alpine-chalet','snow-lodge','arctic-apartment','adobe-home','tropical-stilt-home','tropical-villa','toy-candy-pot','toy-block-apartment','toy-sugar-manor'],
'special':['warehouse','geodesic-dome','tent-home','teacup-house','piggy-bank','bronze-sage-statue','stone-fountain','public-garden','indoor-stadium']}
ASSIGN={0:'jade-skyscraper',1:'office-block',2:'pavilion-apartments',3:'small-temple-chapel',4:'stepped-offices',5:'arctic-apartment',6:'courtyard-mansion',7:'corner-hotel',9:'bronze-sage-statue',10:'stone-fountain',11:'public-garden',12:'public-garden',13:'office-block',14:'food-market',15:'teahouse',16:'post-office',17:'office-block',18:'warehouse',19:'stepped-offices',20:'indoor-stadium',24:'timber-rowhouse',25:'thatched-cottage',26:'courtyard-dwelling',27:'pavilion-apartments',28:'jade-skyscraper',29:'food-market',30:'teahouse',31:'theatre',32:'outdoor-stadium',36:'office-block',37:'alpine-chalet',38:'snow-lodge',39:'cinema',40:'shopping-hall',44:'arctic-apartment',45:'arctic-apartment',46:'alpine-chalet',47:'snow-lodge',48:'alpine-chalet',49:'snow-lodge',50:'stepped-offices',51:'arctic-apartment',52:'office-block',53:'arctic-apartment',54:'jade-skyscraper',55:'arctic-apartment',56:'alpine-chalet',57:'snow-lodge',58:'teahouse',59:'teahouse',60:'city-temple',61:'city-temple',62:'alpine-chalet',63:'snow-lodge',64:'food-market',65:'food-market',66:'corner-hotel',68:'corner-hotel',70:'teahouse',71:'teahouse',72:'slender-apartment',73:'slender-apartment',74:'jade-skyscraper',76:'jade-skyscraper',78:'adobe-home',79:'tropical-stilt-home',80:'tropical-villa',81:'adobe-home',82:'pavilion-apartments',83:'city-temple',84:'tropical-villa',85:'slender-apartment',86:'residential-block',87:'jade-skyscraper',89:'cylindrical-tower',90:'stepped-offices',91:'small-temple-chapel',92:'toy-candy-pot',93:'toy-block-apartment',94:'toy-sugar-manor',95:'toy-candy-pot',96:'toy-block-apartment',97:'toy-sugar-manor',98:'cylindrical-tower',99:'toy-sugar-manor',101:'jade-skyscraper',102:'geodesic-dome',103:'tent-home',104:'toy-candy-pot',105:'teahouse',106:'toy-block-apartment',107:'bronze-sage-statue',108:'teacup-house',109:'piggy-bank'}
def build():
 inv=json.loads((ROOT/'docs/WORLD_ASSET_COVERAGE.json').read_text(encoding='utf-8-sig'));rows=[r for r in inv['items']if r['id'].startswith('house-')]
 mapped=[];parent=None;remain=[]
 for q in rows:
  i=q['neededVariants']['sourceHouseTileId'];flags=q['neededVariants']['buildingFlags'];sizes=[s for s in flags if s.startswith('Size')]
  if sizes:
   size=sizes[0][4:];w,h=map(int,size.split('x'));parent=i
   # GetHouseNorthPart in town_cmd.cpp:3081 shows actual ID order.
   positions=[(0,0),(0,1),(1,0),(1,1)]if(w,h)==(2,2)else([(0,0),(1,0)]if w==2 else([(0,0),(0,1)]if h==2 else[(0,0)]))
   remain=positions.copy();family=ASSIGN[i]
  if not remain:raise RuntimeError('unparented child '+str(i))
  offset=remain.pop(0);par=rows[parent]if parent is not None else q
  row={'sourceHouseId':i,'sourceRequirementId':q['id'],'sourceName':q['name'],'source':q['source'],'parentHouseId':parent,'isParent':parent==i,'tileOffsetXY':list(offset),'footprintTiles':[w,h],'familyId':family,'sourceClimateMasks':q['neededVariants']['climateMasks']or par['neededVariants']['climateMasks'],'sourceMinYear':q['neededVariants']['minYear'],'sourceMaxYear':q['neededVariants']['maxYear'],'sourcePopulation':q['neededVariants']['population'],'sourceBuildingFlags':flags,'randomVariants':[0,1,2,3],'constructionStages':[0,1,2,3],'animationRequired':i in[4,5],'renderGroup':'house-'+str(parent).zfill(3),'artStatus':'planned-awaiting-native-family','mappingBasis':'Source name/climate/footprint -> new Taoist art family; shared family re-design, not a copy of110 distinct OpenTTD paintings.','multiTileRenderPolicy':'whole-family composite plus complementary screen-space partition fragments; exact reassembly tested. Per-fragment runtime depth sorting remains unverified.'}
  mapped.append(row)
 assert len(mapped)==110 and len(set(x['sourceHouseId']for x in mapped))==110
 out={'createdAt':wp.now(),'referenceCommit':inv['referenceCommit'],'sourceHouseTileSpecs':110,'sourceWholeBuildings':sum(x['isParent']for x in mapped),'sourceDrawCombinations':1760,'plannedNativeFamilyCount':sum(map(len,FAMILIES.values())),'sourceDistinctFamilyCount':len(set(x['familyId']for x in mapped)),'nativeFamilyAtlases':FAMILIES,'items':mapped,'footprintSource':[{'file':'src/house.h','line':40},{'file':'src/town_cmd.cpp','line':3081},{'file':'src/town_gui.cpp','line':1402}],'variationPolicy':{'location4':'Four restrained colour grades of actual native family art, not4nativepaintings.','construction4':'shared painted construction/scaffold modules + staged reveal; not4nativebuildingpaintings.','climate':'source climate masks retained; terrain/site material selected from climate. Snow objects/roofs require explicit native source or recorded source-texture masking, not implied by a name.','multiTile':'child IDs share parent family and footprint; no invented independent child building.'},'status':'production contract; not acceptance'}
 wp.writej(ROOT/'docs/HOUSE_PRODUCTION_CONTRACT.json',out)
 print(json.dumps({k:out[k]for k in['sourceHouseTileSpecs','sourceWholeBuildings','sourceDrawCombinations','plannedNativeFamilyCount','sourceDistinctFamilyCount']},ensure_ascii=False))
if __name__=='__main__':build()
