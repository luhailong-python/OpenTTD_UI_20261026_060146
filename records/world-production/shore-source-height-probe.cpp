#include <cstdint>
#include <cstdio>
#include <cstdlib>
constexpr int TILE_SIZE=16,TILE_HEIGHT=8;
#define NOT_REACHED() std::abort()
enum Slope:uint8_t{
	SLOPE_FLAT     = 0x00,                                  ///< a flat tile
	SLOPE_W        = 0x01,                                  ///< the west corner of the tile is raised
	SLOPE_S        = 0x02,                                  ///< the south corner of the tile is raised
	SLOPE_E        = 0x04,                                  ///< the east corner of the tile is raised
	SLOPE_N        = 0x08,                                  ///< the north corner of the tile is raised
	SLOPE_STEEP    = 0x10,                                  ///< indicates the slope is steep
	SLOPE_NW       = SLOPE_N | SLOPE_W,                     ///< north and west corner are raised
	SLOPE_SW       = SLOPE_S | SLOPE_W,                     ///< south and west corner are raised
	SLOPE_SE       = SLOPE_S | SLOPE_E,                     ///< south and east corner are raised
	SLOPE_NE       = SLOPE_N | SLOPE_E,                     ///< north and east corner are raised
	SLOPE_EW       = SLOPE_E | SLOPE_W,                     ///< east and west corner are raised
	SLOPE_NS       = SLOPE_N | SLOPE_S,                     ///< north and south corner are raised
	SLOPE_ELEVATED = SLOPE_N | SLOPE_E | SLOPE_S | SLOPE_W, ///< bit mask containing all 'simple' slopes
	SLOPE_NWS      = SLOPE_N | SLOPE_W | SLOPE_S,           ///< north, west and south corner are raised
	SLOPE_WSE      = SLOPE_W | SLOPE_S | SLOPE_E,           ///< west, south and east corner are raised
	SLOPE_SEN      = SLOPE_S | SLOPE_E | SLOPE_N,           ///< south, east and north corner are raised
	SLOPE_ENW      = SLOPE_E | SLOPE_N | SLOPE_W,           ///< east, north and west corner are raised
	SLOPE_STEEP_W  = SLOPE_STEEP | SLOPE_NWS,               ///< a steep slope falling to east (from west)
	SLOPE_STEEP_S  = SLOPE_STEEP | SLOPE_WSE,               ///< a steep slope falling to north (from south)
	SLOPE_STEEP_E  = SLOPE_STEEP | SLOPE_SEN,               ///< a steep slope falling to west (from east)
	SLOPE_STEEP_N  = SLOPE_STEEP | SLOPE_ENW,               ///< a steep slope falling to south (from north)

	};
unsigned probe(int x,int y,int corners){switch(corners){
		case SLOPE_FLAT: return 0;

		/* One corner is up.*/
		case SLOPE_N: return x + y <= (int)TILE_SIZE ? (TILE_SIZE - x - y)     >> 1 : 0;
		case SLOPE_E: return y >= x                  ? (1 + y - x)             >> 1 : 0;
		case SLOPE_S: return x + y >= (int)TILE_SIZE ? (1 + x + y - TILE_SIZE) >> 1 : 0;
		case SLOPE_W: return x >= y                  ? (x - y)                 >> 1 : 0;

		/* Two corners next to each other are up. */
		case SLOPE_NE: return (TILE_SIZE - x) >> 1;
		case SLOPE_SE: return (y + 1) >> 1;
		case SLOPE_SW: return (x + 1) >> 1;
		case SLOPE_NW: return (TILE_SIZE - y) >> 1;

		/* Three corners are up on the same level. */
		case SLOPE_ENW: return x + y >= (int)TILE_SIZE ? TILE_HEIGHT - ((1 + x + y - TILE_SIZE) >> 1) : TILE_HEIGHT;
		case SLOPE_SEN: return y < x                   ? TILE_HEIGHT - ((x - y)                 >> 1) : TILE_HEIGHT;
		case SLOPE_WSE: return x + y <= (int)TILE_SIZE ? TILE_HEIGHT - ((TILE_SIZE - x - y)     >> 1) : TILE_HEIGHT;
		case SLOPE_NWS: return x < y                   ? TILE_HEIGHT - ((1 + y - x)             >> 1) : TILE_HEIGHT;

		/* Two corners at opposite sides are up. */
		case SLOPE_NS: return x + y < (int)TILE_SIZE ? (TILE_SIZE - x - y) >> 1 : (1 + x + y - TILE_SIZE) >> 1;
		case SLOPE_EW: return x >= y ? (x - y) >> 1 : (1 + y - x) >> 1;

		/* Very special cases. */
		case SLOPE_ELEVATED: return TILE_HEIGHT;

		/* Steep slopes. The top is at 2 * TILE_HEIGHT. */
		case SLOPE_STEEP_N: return (TILE_SIZE - x + TILE_SIZE - y) >> 1;
		case SLOPE_STEEP_E: return (TILE_SIZE + 1 + y - x) >> 1;
		case SLOPE_STEEP_S: return (1 + x + y) >> 1;
		case SLOPE_STEEP_W: return (TILE_SIZE + x - y) >> 1;

		default: NOT_REACHED();
	}}
int main(){int codes[]={1,2,3,4,6,7,8,9,11,12,13,14,27,23,30,29};for(int c:codes)for(int y=0;y<=16;y++)for(int x=0;x<=16;x++)std::printf("%d,%d,%d,%u\n",c,x,y,probe(x,y,c));}
