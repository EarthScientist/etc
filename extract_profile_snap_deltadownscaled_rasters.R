require(raster)
require(rgdal)

# set a working dir
setwd("./working")

# set a folder location to where the files are stored on your system. 
# in this case I am going into the CRU historical precip data
input_path <- "./downscaled/CRU-TS40/historical/pr"

# point to the point shapefile you want to use.
# [note]: you may have to reproject these points to the same reference system as the SNAP data (EPSG:3338)
pointSPDF <- readOGR("./shapefile/points.shp")

# stuff which will be iterators through the years/months
years <- 1901:2009
months <- c("01","02","03","04","05","06","07","08","09","10","11","12")

# naming stuff to get everything in the list chronologically
variable <- "pr"
metric <- "total_mm"
model <- "CRU-TS40"

# list the files chronologically. this is ugly and can be improved, but is a way to do it.
list.2km <- character()
for(y in years){
	for(m in months){
		name_convention <- paste(input_path,variable,"_",metric,"_",model,"_",'historical',"_",m,"_",y,".tif", sep="")
		list.2km <- append(list.2km, name_convention)
	}
}

# read the files we just listed as a raster stack
s <- stack(list.2km)
extraction <- extract(s, pointSPDF)

# then transpose it so the point locs are in the cols, and the samples are in the rows
extraction <- t(extraction)

# from here you should be able to dump these to CSV or work with the values in subsequent R functions.
