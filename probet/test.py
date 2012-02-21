import re

row = re.compile('.*<tr class="(even|odd)">', re.M | re.S )
end = re.compile('.*</tr>')
f = open('odds.html')


scoop = False
hand = ''
dump = []
for line in f:
    
    if scoop:
        if end.match(line):
            scoop = False
            #drop in string
            dump.append('<tr>'+hand+'</tr>')
            hand = ''
        else:
            #build string
            hand += line
    else:
        if row.match(line):
            scoop = True

print dump