
import numpy as np
from osgeo import gdal



# Chargement du fichier

filename = 'elevation_data/viewfinderdata/merged_1arc.hgt'
# cf http://www.viewfinderpanoramas.org/dem3.html#alps
dataset = gdal.Open(filename)



R = 6371.009 # km, rayon moyen de la terre


""" Transformation des coordonnés (lon, lat) en degrée decimaux  vers les pixels
    et inversement
""" 
transf = dataset.GetGeoTransform()
transfInv = gdal.InvGeoTransform(transf)

def transf_to_px( coords ):
    px = gdal.ApplyGeoTransform(transfInv, *coords)
    return [ int( x ) for x in px ]

def transf_to_deg( pxy ):
    return gdal.ApplyGeoTransform(transf, *pxy )


""" Permet d'obtenir l'altitude d'un point   en mètre
    xy: tuple coordonnées en pixel
"""

band = dataset.GetRasterBand(1)
elevation = band.ReadAsArray()

def get_ele( xy ):
    return elevation[ xy[1] , xy[0] ]

# --- 

def torad( theta ):
    """ convert to radian
    """
    return theta * np.pi / 180.0

def get_theta( lon1, lat1, lon2, lat2 ):
    """ Calcul l'angle entre deux positions sur terre
    """
    lat1, lon1, lat2, lon2 = [ torad(theta) for theta in [lat1, lon1, lat2, lon2] ]
    cosTheta =  np.sin( lat1 )*np.sin( lat2 ) + np.cos( lat1 )*np.cos( lat2 )*np.cos( lon2-lon1 )
    
    cosTheta = np.array( cosTheta )
    cosTheta[ cosTheta> 1 ] = 1  # debug .... cas si lat1==lat2 et lon1 == lon2
    
    theta = np.arccos( cosTheta )
    
    return theta # en radian




def is_visible( latA, lonA, latB, lonB ): 
    """ Determine si le point B est visible depuis le point A
        lonA, latA: longitude et lattitude du point A, en degrée décimaux
        
        return True/False
    """
    coordsA = ( lonA, latA ) 
    coordsB = ( lonB, latB ) 

    pxA, pxB = transf_to_px( coordsA ), transf_to_px( coordsB )
    
    
    """ Test si hors map -> alors non visible 
    """
    if pxA[0] >= elevation.shape[0] or pxA[1] >= elevation.shape[1]  or \
       pxB[0] >= elevation.shape[0] or pxB[1] >= elevation.shape[1]  or \
       pxA[0] < 0  or pxA[1] < 0 or \
       pxB[0] < 0  or pxB[1] < 0  :
         return False
         
    
    """ Calcul du nombre de point pour l'interpolation
    """
    # Distance entre A et B en pixel
    L = np.sqrt( (pxA[0]-pxB[0])**2 +  (pxA[1]-pxB[1])**2  )

    # nombre de points  pour l'interpolation entre A et B
    N = int( np.floor( L/5 ) )  # <- facteur 

    # test si point trop proche :
    if N < 6:
        return True

    # interpolation linéaire entre A et B :
    x_span = np.linspace( pxA[0], pxB[0], N )
    y_span = np.linspace( pxA[1], pxB[1], N )

    pxy_span = np.array( [ x_span, y_span ] ).T
    ele_span = [ get_ele( pxy_int ) for pxy_int in pxy_span.astype(int) ]
    
    deg_span = np.array( [ transf_to_deg( pxy ) for pxy in pxy_span ] )

    theta_span = get_theta( *coordsA , deg_span[:, 0], deg_span[:, 1] )


    delta_courbure = R*( 1- np.cos(theta_span[-1]/2 )/np.cos( theta_span - theta_span[-1]/2 ) )*1e3

    elevation_reel = np.array( ele_span )  + delta_courbure

    # **Le sommet est visible si la différence entre la _ligne de vue_ et le profil de hauteur est toujours postive. **

    # Calcul de l'angle de vue :
    x = R*np.array( theta_span )
    y = elevation_reel

    view_angle = (y[1:] - y[0])/(x[1:] - x[0])
    visible = ((view_angle[-1] - view_angle[:-1]) > 0 ).all()

    return visible





# # pour la suite
# 
# * faire l'interpolation proprement en coord. sphérique
# * prendre en compte la refraction de l'air
# 
# 
# * Calcul de la position de l'horizon et des zones visibles
# 
# voir aussi [sherrytowers.com -calculating-the-horizon-profile](http://sherrytowers.com/2014/04/13/archeoastronomy-calculating-the-horizon-profile-using-online-us-geographic-survey-data/)




