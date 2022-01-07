# -*- coding: utf-8 -*-
from scrapy import Spider, Request
from urlparse import urlparse
import sys
import re, os, requests, urllib
from scrapy.utils.response import open_in_browser
from collections import OrderedDict
import time
from shutil import copyfile
import json, re


def download(url, destfilename):
	if not os.path.exists(destfilename):
		print "Downloading from {} to {}...".format(url, destfilename)
		try:
			r = requests.get(url, stream=True)
			with open(destfilename, 'wb') as f:
				for chunk in r.iter_content(chunk_size=1024):
					if chunk:
						f.write(chunk)
						f.flush()
		except:
			print "Error downloading file."

class YlightingSpider(Spider):
	name = "artek"
	#start_urls = ['http://www.yliving.com/brand/URBN/_/N-1sm7c']
	start_urls = [
			#'http://www.yliving.com/brand/NEMO/_/N-1sbfa'
			'http://www.yliving.com/brand/Artek/_/N-1sbch']

	#brand_name = "URBN"
	brand_name = "Artek"

	use_selenium = True
	count = 0
	reload(sys)
	sys.setdefaultencoding('utf-8')

	def filter_list(self, lst):
		min_len = min([len(x) for x in lst])
		sp = -1
		for x in xrange(0,min_len-1):
			fst = set([i[0] for i in lst])
			if len(fst) <= 1:
				lst = [i[1:] for i in lst]
			else:
				break
		return lst

	def extract_models(self, data):
		if 'vpn' in data:
			yield data['vpn'].split('|')[0]
		for k in data:
			if isinstance(data[k], dict):				
				for i in self.extract_models(data[k]):
					yield i


	def extract_colors(self, data, name):
		if name in data:
			for k in data[name]:
				yield data[name][k]['name']
		else:
			for i in data:
				if isinstance(data[i], dict):
					for j in data[i]:
						for n in self.extract_colors(data[i][j], name):
							yield n


	def extract_images(self, data):
		if 'image' in data:
			yield {data['name']:data['image']}

		for k in data:
			if isinstance(data[k], dict):				
				for i in self.extract_images(data[k]):
					yield i

	def extract_swatches(self, data, name):
		if name in data:
			for k in data[name]:
				yield {data[name][k]['name']:data[name][k]['image']}
		else:
			for i in data:
				if isinstance(data[i], dict):
					for j in data[i]:
						for n in self.extract_swatches(data[i][j], name):
							yield n

	def insert_lastone(self, title):
		m = title.split()
		m[-1], m[-2] = m[-2], m[-1]
		return ' '.join(m)

	def insert_one(self, title):
		print "#######",title
		splitter = " - "
		
		s,l = title.split(splitter)

		s = s.replace('Wall Sconce','Wallsconce').replace('Suspension System','SuspensionSystem').replace('Light Suspension','LightSuspension').\
				replace('Suspension Light','SuspensionLight').replace('/','').replace('Wall Light','Walllight').replace('Light Pendant','LightPendant').\
				replace('Ceiling Fan','CeilingFan').replace('Wall Fan','WallFan')

		l = l.replace(' / ',' ').replace('-','')
		result = list(s.split())
		result.insert(-1, l.strip())
		return ' '.join(result)

	def parse(self, response):
		products = response.xpath('//*[@class="record__image image"]/@href').extract()
		print len(products)
		for product in products:
			yield Request(response.urljoin(product), callback=self.parse_product)
			#break	
			
		next = response.xpath('//*[@class="icon-angle-right"]/parent::*[1]/@href').extract()
		if next:
			yield Request(response.urljoin(next[0]), callback=self.parse)


	def parse_product(self, response):

		collections = ['Rival', 'H55', 'Domus','Kiki','Lukki','Mademoiselle','Pirkka','Siena'
					]
		item = OrderedDict()

		productInfo = json.loads(re.findall('var productData = (\{.*\});',response.body)[0])
		title = productInfo['name']#' '.join(response.xpath('//h1[@itemprop="name"]//text()').extract()).strip().replace('New', '').strip()

		title = title.replace('&Eacute;','E')
		if "Open Box" in title or "Bag " in title:
			return



		item['src'] = response.url
		item['Title'] = title

		title = title.replace('&reg;','').replace('&trade;','').replace('&eacute;','e').replace('&amp;','').replace('&quot;','')
		if "Paimio" in title or "Rival" in title or 'Children\'s Chair' in title or "Table 8" in title or "Table 9" in title or "Table Y8" in title:
			title = self.insert_lastone(title)

		title = title.replace(', Set of 2','').replace('Big Bang','Bigbang').replace('Diesel Collection','DieselCollection').replace('Le Soleil','LeSoleil').\
				replace('New Buds','Newbuds')

		temp_id = 'artek '+title.lower().replace('-','').replace('.','').replace('\'','').replace('/',' ').\
						replace('&ucirc;','u').replace('spun light','spunlight').replace('string light','stringlight').replace('miss k','missk').replace('top top','toptop')

		
		temp_id = temp_id.replace('floor lamp','floorlamp').replace('desk lamp','desklamp').replace('table lamp', 'tablelamp').\
					replace('pendant light','pendantlight').replace('desk light','desklight').replace('wall light', 'walllight').replace('wall sconce', 'wallsconce').\
					replace('path light','pathlight').replace('ceiling light', 'ceilinglight').replace('recessed light','recessedlight').replace('gift set','giftset').\
					replace('suspension light','suspensionlight').replace('wall lamp','walllamp').replace('ceiling lamp','ceilinglamp').replace('pendant lamp','pendantlamp').\
					replace('seat pad','seatpad').replace('pedestal fan','pedestalfan').replace('ceiling fan','ceilingfan').replace('wall control','wallcontrol').\
					replace('remote control','remotecontrol').replace('caster set','casterset').replace('side table','sidetable').replace('chair set','chairset').\
					replace('bath bar','bathbar').replace('flush mount','flushmount').replace('suspension system','suspensionsystem').\
					replace('lighting system','lightingsystem').replace('hanger kit','hangerkit').replace('bath light','bathlight').replace('vanity kit','vanitykit').\
					replace('vanity light','vanitylight').replace('mirror kit','mirrorkit').replace('suspension lamp','suspensionlamp')

		# temp code start
		# yield item
		# return
		# temp code end

		words = temp_id.split(' ')
		id = 'artek-' + ''.join(words[1:-1]) + '-' + words[-1]
		try:
			print words[1].title()
			if words[1].title() in collections:
				id = id + "-" + words[1].lower()
		except:
			print words[0].title()
			if words[0].title() in collections:
				id = id + "-" + words[0].lower()

		# ID Exception process
		if id == "artek-tankarmchair400,hellajongeriusspecial-edition":
			id = "artek-tank400hellajongeriusspecialedition-armchair"
		if id == "artek-armchair-26":
			id = "artek-26-armchair"
		if id == "artek-armchair401,hellajongeriusspecial-edition":
			id = "artek401hellajongeriusspecialedition-armchair"
		if id == "artek-armchair-42":
			id = "artek-42-armchair"
		if id == "artek-bench-153":
			id = "artek-153-bench"
		if id == "artek-chair-23":
			id = "artek-23-chair"
		if id == "artek-chair-66":
			id = "artek-66-chair"
		if id == "artek-chair-69":
			id = "artek-69-chair"
		if id == "artek-extensiontable-h92":
			id = "artek-extensionh92-table"
		if id == "artek-hallwaychair-403":
			id = "artek-hallway403-chair"
		if id == "artek-nestingtable88,setof-3":
			id = "artek-88setof3nesting-table"
		if id == "artek-sidetable-606":
			id = "artek-606-sidetable"
		if id == "artek-sidetable-915":
			id = "artek-915-sidetable"
		if id == "artek-sienacoasters,2piece-set-siena":
			id = "artek-siena2piecesetsiena-coasters"
		if id == "artek-sienateatowel,2piece-set-siena":
			id = "artek-siena2pieceset-teatowel-siena"
		if id == "artek-stool-60":
			id = "artek-60-stool"
		if id == "artek-stool60,hellajongeriusspecial-edition":
			id = "artek-60hellajongeriusspecialedition-stool"
		if id == "artek-stool-e60":
			id = "artek-e60-stool"
		if id == "artek-stoole60,anniversary-edition":
			id = "artek-e60anniversaryedition-stool"
		if id == "artek-teatrolley-900":
			id = "artek-900-teatrolley"
		if id == "artek-teatrolley-901":
			id = "artek-901-teatrolley"
		if id == "artek-triennacoffee-table":
			id = "artek-trienna-coffeetable"
		if id == "artek-wallshelf-112a":
			id = "artek-112a-wallshelf"
		if id == "artek-wallshelf-112b":
			id = "artek-112b-wallshelf"


		# ID Exception process
		item['id'] = id

		self.count += 1
		print "######################  ", self.count
		print response.url


		# temp code start
		# yield item
		# return 
		# temp code end
		item['modelno'] = list(set(list(self.extract_models(productInfo))))#response.xpath('//*[@class="ellipsis"]/text()').extract_first().strip()
		item['available'] = "1-2 Weeks"
		item['sale-price'] = ''
		item['call-price'] = ''
		item['price'] = productInfo['lowest_price']#response.xpath('//*[contains(@class, "current-price")]/text()').re('[\d,]+')[0].replace(',','')
		item['pbrand'] = 'artek'
		code = ''
		item['finish'] = '' ###
		lamp_type = response.xpath('//*[@id="tab-specs"]//*[contains(text(),"Lamp Type")]/parent::*[1]//text()').extract()
		lamp_type = filter(None, list(x.strip() for x in lamp_type))
		lamp_type = list(set(lamp_type))
		if "Lamp Type" in lamp_type:
			lamp_type.remove("Lamp Type")
		item['bulb'] = ''.join(' '.join(lamp_type).split(' '))
		item['bulb'] = '"' + '","'.join(item['bulb'].split(',')) + '"'
		voltage = response.xpath('//*[@id="tab-specs"]//*[contains(text(),"Bulbs")]/parent::*[1]//text()').re('(\d+V)')
		if voltage:
			item['voltage'] = '"' + '","'.join(list(set(voltage))) + '"'
		else:
			item['voltage'] = ''

		swatches = []
		### Color options ###
		item['pcolor'] = ''
		attributesKey = productInfo['attributeKey']
		if attributesKey:
			colorAttr = {}
			for i, attr in enumerate(attributesKey):
				if "Color" in attr['name'] or "Finish" in attr['name']:
					colorAttr = attr.copy()
					break
			if colorAttr:
				# try:
				# 	options = productInfo['attributes'][colorAttr['id']]
				# except:
				# 	item['pcolor'] = ''
				# else:
				# 	for option_key in options.keys():
				# 		item['pcolor'] = item['pcolor'] + '"' + options[option_key]['name'] + '"' + ' or '
			
				# 	item['pcolor'] = item['pcolor'].strip(' or ')
				
				colors = list(self.extract_colors(productInfo['attributes'], colorAttr['id']))
				swatches = list(self.extract_swatches(productInfo['attributes'], colorAttr['id']))
				colors = list(set(colors))
				item['pcolor'] = '"'+'" or "'.join(colors)+'"'

		

		### Dimensions ###
		dimensions = response.xpath('//*[@id="tab-specs"]//*[text()="Dimensions"]/following-sibling::*[1]//text()').extract()
		dimensions = filter(None, list(x.strip() for x in dimensions))
		dimensions = list(set(dimensions))
		widths = []
		heights = []
		weight = ""
		display_dimensions = ""
		print dimensions
		if dimensions:
			display_dimensions = "<div>"
			for dimension in dimensions:
				display_dimensions += "<li>" + dimension + "</li>"
				width = ''.join(re.findall('([.\d]+?)\"\s*W', dimension))
				height = ''.join(re.findall('([.\d]+?)\"\s*H', dimension))
				w = ''.join(re.findall('([.\d]+\s*lbs?)', dimension))
				if w:
					width = w[0]

				if width:
					if ":" in dimension:
						width = '"' + dimension.split(':')[0] + ':" "' + width + 'in"'
					else:
						width = '"Width:" "' + width + 'in"'
				if height:
					if ":" in dimension:
						height = '"' + dimension.split(':')[0] + ':" "' + height + 'in"'
					else:
						height = '"Height:" "' + height + 'in"'
				widths.append(width)
				heights.append(height)
		item['width'] = ','.join(widths).strip(',')
		item['height'] = ','.join(heights).strip(',')
		if display_dimensions:
			display_dimensions += "</div>"
		item['display-dimensions'] = display_dimensions

		if weight:
			item['weight'] = '"' + w + '"'
		item['weight'] = ""
		item['options'] = ""
		lowest_price = float(productInfo['lowest_price'])
		attributekey = productInfo['attributeKey']
		code = ""
		options = ""
		if attributekey:			
			if len(attributekey) == 1:
				child_products = productInfo['attributes'][attributekey[0]['id']]
				options = '[\"{}:\"] '.format(attributekey[0]['name'])
				id_list = self.filter_list([child_products[x]['vpn'].split('|')[0].strip() for x in child_products.keys()])
				for idx, child_key in enumerate(child_products.keys()):
					child_product = child_products[child_key]
					option = '\"[-{}]{}'.format(id_list[idx], child_product['name'])
					current_price = float(child_product['price'])
					if current_price > lowest_price:
						option += '(+${})\" '.format(str(current_price-lowest_price))
					else:
						if current_price == lowest_price:
							code = child_product['vpn'].split('|')[0].strip()
						option += '\" '
					options += option
				options = options.strip()

			if len(attributekey) == 2:
				options = '[\"Versions:\"] '
				child_products = productInfo['attributes'][attributekey[0]['id']]
				
				for idx, child_key in enumerate(child_products.keys()):
					child_product = child_products[child_key]
					grand_child_products = child_product[attributekey[1]['id']]
					id_list = self.filter_list([grand_child_products[x]['vpn'].split('|')[0].strip() for x in grand_child_products.keys()])
					for idx1, grand_cihld in enumerate(grand_child_products.keys()):
						grand_cihld_product = grand_child_products[grand_cihld]

						option = '\"[-{}]{}/{}'.format(id_list[idx1], child_product['name'], grand_cihld_product['name'])
						current_price = float(grand_cihld_product['price'])
						if current_price > lowest_price:
							option += '(+${})\" '.format(str(current_price-lowest_price))
						else:
							if current_price == lowest_price:
								code = grand_cihld_product['vpn'].split('|')[0].strip()
							option += '\" '
						options += option
				options = options.strip()

			if len(attributekey) == 3:
				options = '[\"Versions:\"] '
				child_products = productInfo['attributes'][attributekey[0]['id']]
				
				for idx, child_key in enumerate(child_products.keys()):
					child_product = child_products[child_key]
					grand_child_products = child_product[attributekey[1]['id']]
					
					for idx1, grand_cihld in enumerate(grand_child_products.keys()):
						grand_cihld_product = grand_child_products[grand_cihld]
						grand_grand_child_products = grand_cihld_product[attributekey[2]['id']]
						id_list = self.filter_list([grand_grand_child_products[x]['vpn'].split('|')[0].strip() for x in grand_grand_child_products.keys()])
						for idx2, grand_grand_child in enumerate(grand_grand_child_products.keys()):
							grand_grand_cihld_product = grand_grand_child_products[grand_grand_child]
							option = '\"[-{}]{}/{}/{}'.format(id_list[idx2], child_product['name'], grand_cihld_product['name'], grand_grand_cihld_product['name'])
							current_price = float(grand_grand_cihld_product['price'])
							if current_price > lowest_price:
								option += '(+${})\" '.format(str(current_price-lowest_price))
							else:
								if current_price == lowest_price:
									code = grand_grand_cihld_product['vpn'].split('|')[0].strip()

								option += '\" '
							options += option
				options = options.strip()
			else:
				pass
		
		item['options'] = options

		

		if code:
			item['modelno'] = code

		designers = response.xpath('//*[@id="tab-designer"]//*[@class="h2"]/text()').extract()

		item['designer'] = '"' + '" and "'.join(designers) + '"'

		item['mss-made-in'] = 'England'
		item['brandlink'] = 'artek'
		item['designer-link'] = ','.join(designers)

		
		#modelnos = ''.join(response.xpath('//*[@id="tab-specs-desktop"]//*[contains(text(), "Model")]/following-sibling::*/text()').extract())
		# modelnos = response.xpath('//b[contains(text(), "Model")]/following-sibling::*/text()').extract_first()
		# if not modelnos:
		modelnos = ' '.join(list(set(list(self.extract_models(productInfo)))))
		# else:
		# 	modelnos = modelnos.strip()
		# 	item['modelno'] = re.findall(r'\d{4,4}',modelnos)[0]

		item['modelnos'] = modelnos
		
		item['shape'] = ''
		item['qualifications'] = ''
		item['related-items'] = ''
		item['Tags'] = ''
		item['Notes'] = ''
		item['Warranty'] = '"1 Year"'
		item['prioritization'] = ''
		item['product-categories'] = ''
		item['product-type-filters'] = ''
		item['collection-placement'] = "artek-"+id.split('-')[-1] if id.split('-')[-1].title() in collections else ''
		item['expiration-date'] = ''

		for x in xrange(1,19):
			key = "mss-pdf{}".format(x)
			item[key] = ''
			key = "mss-pdf-text{}".format(x)
			item[key] = ''

		pdfs = response.xpath('//*[contains(@href, ".pdf")]/@href').extract()
		if pdfs:
			pdf_path = "{}/PDF/".format(self.brand_name)
			if not os.path.exists(pdf_path):
				os.makedirs(pdf_path)

			pdfs = list(set(pdfs))
			for idx, pdf in enumerate(pdfs):
				filename = id + "-pdf" + str(idx+1) + ".pdf"
				download(response.urljoin(pdf), pdf_path+filename)
				
		# IMAGE
		images_list = response.xpath('//*[contains(@class, "carousel-indicators mCustomScrollbar")]//img/@src').extract()
		if not images_list:
			images_list = set(response.xpath('//*[@class="productDetail-carousel-image"]/@src').extract())
		images = list("http://www.yliving.com"+x for x in images_list)

		filename = None
		image_path = None
		for x in xrange(0,50):
			key = "image{}".format(x+1)
			try:
				image = images[x]
			except:
				image = ''

			if not image:
				item[key] = ''
			else:
				image_path = "{}/Images/".format(self.brand_name)

				if not os.path.exists(image_path):
					os.makedirs(image_path)

				extension = image.split('.')[-1]
				filename = id
				if x > 0:
					filename = filename + "-image{}".format(x)
				item[key] = filename

				filename = filename + "." + extension
				download(image, image_path+filename)

		item['inset'] = id+'-schematic'
		schematic_path = "{}/Schematics/".format(self.brand_name)
		if not os.path.exists(schematic_path):
			os.makedirs(schematic_path)
		if filename:
			dest_file = schematic_path+item['inset']+"."+filename.split('.')[-1]
			if not os.path.exists(dest_file):
				copyfile(image_path+filename, dest_file)
		# Finishes
		#item['finish'] = '"Natural"' if "table" in id or "chair" in id else ""
		# Swatches

		


		print "@@@@@@@@@@@@@@@@@"
		print len(swatches)
		print swatches
		pcolor = ''
		for x in xrange(0,50):
			key1 = "color-image-{}".format(x+1)
			key2 = "color-text-{}".format(x+1)
			
			item[key1] = ''
			item[key2] = ''

			try:
				swatch = swatches[x]
			except:
				continue
			else:				
				swatch_overlay = swatch.keys()[0]

				swatch_url = 'http://www.ylighting.com/tiles/{}/{}'.format(response.url.split('/')[-1].replace('.html',''),swatch[swatch_overlay])

				image_path = "{}/Swatches/".format(self.brand_name)
				if not os.path.exists(image_path):
					os.makedirs(image_path)
				extension = swatch_url.split('.')[-1]
				filename = id+'-'+swatch_overlay.lower().replace(' ','').replace('/','')
				item[key1] = filename
				item[key2] = swatch_overlay
				filename = filename + "." + extension
				download(swatch_url, image_path+filename)
				pcolor = pcolor + '"' + swatch_overlay + '"' + ' or ' 

		item['pcolor'] = pcolor.strip(' or ')
		item['name'] = title
		caption = '<b>Artek ' + title + '</b><br>' + ' '.join(response.xpath('//*[@id="tab-specs-desktop"]//*[@class="p"]/p[position() > 1]/text()').extract())
		item['caption'] = caption
		item['Custom-title'] = title
		item['Custom-description'] = ''
		item['Custom-keyword'] = 'artek,' + ','.join(title.split(',')[0].replace('/',' ').lower().split(' '))
		item['Custom-headline'] = title
		item['Freight'] = ''
		
		#item['Base-material'] = 'Wood'
		materials = response.xpath('//*[@id="tab-specs"]//*[contains(text(),"Material")]/parent::*[1]//text()').extract()
		materials = list(set(filter(None, list(x.strip() for x in materials))))
		
		item['finish'] = ' '.join(materials).replace('Material(s)','').strip()
		item['Base-material'] = ''#material

		# images_list = response.xpath('//*[contains(@class, "carousel-indicators mCustomScrollbar")]//img/@src').extract()
		# if not images_list:
		# 	images_list = set(response.xpath('//*[@class="productDetail-carousel-image"]/@src').extract())

		# images = list("http://www.yliving.com"+x for x in images_list)

		# item['images'] = images
		yield item