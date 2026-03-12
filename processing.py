from numpy import clip , uint8 , array , prod 
from PIL import Image
def load_image(path = ''):
    img = Image.open(path)
    gray_img = img.convert("L")
    gray_array = array(gray_img)
    return gray_array

def adjust_brightness(img , beta):
    temp_img = img + beta
    temp_img = clip(temp_img , 0 , 255).astype(uint8)
    return temp_img

def linear_contrast(img , alpha , beta):
    temp_img = alpha * img 
    temp_img = adjust_brightness(temp_img , beta)
    return temp_img

def contrast_strech(img , f_min = None , f_max = None):
    f_min = f_min if f_min is not None else img.min()
    f_max = f_max if f_max is not None else img.max()
    divisor = f_max - f_min if f_max != f_min else 255
    temp_img = 255 * (img - f_min) / divisor
    return clip(temp_img , 0 , 255).astype(uint8)
    
def compute_histogram(img):
    H = array([img[img == pixel].shape[0] for pixel in range(256)])
    return H

def compute_cdf(img):
    H = compute_histogram(img)
    size  = prod(img.shape)
    probabilities = H / size
    C = [sum(probabilities[:i+1]) for i in range(256)]
    return C

def histogram_equalization(img):
    C = compute_cdf(img)
    C_normalized = [int(255 * c) for c in C]
    equalized_img = array([C_normalized[pixel] for pixel in img.flat]).reshape(img.shape)
    print(equalized_img)
    return equalized_img.astype(uint8)

def threshold(img , threshold):
    temp = img >= threshold
    return temp * 255 
