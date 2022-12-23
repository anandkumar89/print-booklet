import PyPDF2 as pdf
from PyPDF2.generic import AnnotationBuilder
from tqdm import tqdm
from math import ceil

def crop(page, l=0, b=0, r=0, t=0, flip=False):
    if flip:
        temp = r; r = l; l = temp
    page.trimBox.setLowerLeft([a+b for a, b in zip(page.trimBox.lower_left, (l, b))])
    page.trimBox.setUpperRight([a-b for a, b in zip(page.trimBox.upperRight, (r, t))])
    page.mediaBox = page.trimBox
    page.cropBox  = page.trimBox
    return page

def createBooklet(pdfpath, mo=10, mc=40, mt=0, crop=False, crop_tuple=[], alternateCrop=True):
    '''
    mo : margin open
    mc : margin center
    mt : if and bottom margin is assymetrical, subtract from top. !warning mt is used to calculate scale, why? if want to force margin in tight crops remove from scale calc and it'll serve original purpose. 
    '''
    outpdf = pdf.PdfFileWriter()
    tarw, tarh = 595 , 842  # paper size (1"=72 points)

    inpdf   = pdf.PdfFileReader(open(pdfpath, 'rb'), strict=True)
    numpage = inpdf.getNumPages()
    start = 1; end = numpage # start and end page number (both included), will not work don't change ###fix later
    
    line = AnnotationBuilder.line(
        text="Hello world",
        rect=(0, 421, 596, 421),
        p1=(0, 421),
        p2=(596, 421),
    )
    rectr = AnnotationBuilder.line(
        text="hello",
        rect=(mo, 421+mc, 596-mo, 842-mo),
        p1 = (mo+50, 421+mc), 
        p2=(596-mo-50, 421+mc),
    )
    rectl = AnnotationBuilder.line(
        text="hello",
        rect=(mo, mo, 596-mo, 421-mc),
        p1 = (mo+50, 421-mc), 
        p2=(596-mo-50, 421-mc),
        )

    # move this block inside for loop after crop, if cropping the page. ATTENTION!
    tp = inpdf.getPage(start) # typical page, 

    nr = start-1; nl = end if (end-start+1)%2!=0 else end-1; nl = nl if (nl+1)%4==0 else end + 2
    for pnum in tqdm(range(ceil((nl+1)/2))):
        pr = inpdf.getPage(nr)
        pl = inpdf.getPage(nl) if nl<end else None
        
        # Trim margins from right and left, doesn't work now
        # if crop:
        #     pl = crop(pl, *crop_tuple, alternateCrop if nl%2==1 else not alternateCrop)
        #     pr = crop(pr, *crop_tuple, alternateCrop if nl%2==1 else not alternateCrop)

        scale = min(tarw/(float(tp.cropBox.height)+2*mt), (tarh-2*mc-2*mo)/float(tp.cropBox.width)/2) ## assume all pages have same cropBox - helps in case of odd pages
        w_sc  = float(pr.cropBox.width)*scale
        mc    = max(mc, (tarh-2*mo-2*w_sc)/2)
        mt    = (tarw - float(tp.cropBox.height)*scale)/2 - float(tp.cropBox.lower_left[1])*scale
        tyl   = mo                                        - float(tp.cropBox.lower_left[0])*scale/(-1 if pnum%2!=0 else 1)
        tyr   = mo + w_sc + 2*mc                          - float(tp.cropBox.lower_left[0])*scale/(-1 if pnum%2!=0 else 1)

        if pnum==0:
            print((nl, nr, scale, mo, mc, mt, w_sc, tyl, tyr))
            print(tp.mediaBox)
            print(tp.cropBox)
            print(tp.trimBox)

        emptyPage = pdf.PageObject.createBlankPage(width=tarw, height=tarh)
        if pnum%2!=0: 
            temp = pl; pl = pr; pr = temp; rot = 270; txl = txr = mt;
            temp = tyl; tyl = tyr; tyr = temp; 
            tyr += w_sc; tyl += w_sc
        else: 
            rot = 90; txl = txr = tarw - mt
        
        if pr!=None:
            emptyPage.mergeRotatedScaledTranslatedPage(pr, rot, scale, txr, tyr)
        if pl!=None:
            emptyPage.mergeRotatedScaledTranslatedPage(pl, rot, scale, txl, tyl)

        outpdf.addPage(emptyPage)

        outpdf.add_annotation(page_number=pnum, annotation=line)
        outpdf.add_annotation(page_number=pnum, annotation=rectr)
        outpdf.add_annotation(page_number=pnum, annotation=rectl)

        nr += 1; nl -= 1
    
    outputStream = open(pdfpath.split('/')[-1].split('.')[0]+"_booklet.pdf","wb")
    outpdf.write(outputStream)
    outputStream.close()


#mc 40 works just fine with 30 page print = 60 page bind 
#for tight crops ensure mt, mo be 20 (note that scaled mt will be applied i.e. will be less than specified)
createBooklet("lens_design_cropped.pdf", mc=50, mo=20, mt=20) 
