# List of TLDs and countries obtained initially from
# http://http-analyze.org/tld.php
# and modified by me manually to handle our wacky data

# Bring in data into a dictionary
$countries = Hash.new

File.open("TLD_country.txt","r").each_line do |line|
  data = line.split(/\t/)
  $countries[data[1].strip().downcase()] = data[0].strip().downcase()
end

# Add some manual updates to country hash
$countries[""] = "??"



# The Geonames data sometimes has the same alternative name mapped to
# multiple countries. Read in a disambiguation file I created.
$ambiguous_alternatives = Hash.new
File.open("alternative_map.txt","r").each_line do |line|
  data = line.split(/\t/)
  country_name = data[0].strip()
  country_code = data[1].strip()
  $ambiguous_alternatives[country_name] = country_code
end


# Function to take country name, code, whatever and turn it into
# canonical country code
def resolve_country(domain,raw_country)
  # Assume that if it is already two characters, it is good as it is
  raw_country = raw_country.downcase()
  
  # If country name has a digit in it, assume it is garbage
  if raw_country.match(/\d/)
    return "??"
    
  elsif raw_country.length() == 2 && $countries.has_value?(raw_country)
    return raw_country
    
  elsif $countries.has_key?(raw_country)
    return $countries[raw_country]
    
  else
    puts "Country error"
    puts domain, raw_country
    raise "Can't figure out what to do with country"
    return nil
  end
end  



$alternatives = Hash.new

# Load in GeoNames data that contains country codes and lots of
# alternative names for them
# Layout documentation:
#  http://download.geonames.org/export/dump/
#  http://www.geonames.org/export/codes.html
File.open("justCountries.txt","r").each_line do |line|
  data = line.split(/\t/)
  country_name = data[1].strip().downcase()
  country_code = data[8].strip().downcase()
  alternative_names = data[3].strip().downcase().split(",")

  alternative_names.each { |alt_name|

    # The approach we're using is to do a complete string search to
    # see if the alternative name appears in the whois record. The
    # problem is that some of these alternative names are really
    # short, and we get false matches on prepositions or
    # whatever. Throw the record away if it is three characters or
    # fewer.
    if alt_name.length() <= 3
      next
    end
    
    # Check to make sure the same alternative name isn't in there for
    # two different countries. It is sometimes repeated for the same
    # country with different case.
    if $ambiguous_alternatives.has_key?(alt_name)
      $alternatives[alt_name] = $ambiguous_alternatives[alt_name]

    elsif $alternatives.has_key?(alt_name) and country_code != $alternatives[alt_name]
      puts "Duplicate alternative name: " + alt_name + "\t" + country_code + "\t" + $alternatives[alt_name]

    else
      $alternatives[alt_name] = country_code
    end
  }

end


# Turn alternatives into a regex dictionary, where each key is the
# country code, and each value is the regular expression for
# matching it.
$alts_regex = Hash.new("[^[[:word:]]](")
$alternatives.keys.each do |alt_name|
  $alts_regex[$alternatives[alt_name]] += (alt_name + "|")
end
# Replace extraneous last "or" with paren
$alts_regex.keys.each do |ccode|
  $alts_regex[ccode][-1] = ")"
  $alts_regex[ccode] += "[^[[:word:]]]"
  $alts_regex[ccode] = Regexp.new($alts_regex[ccode])
end



# Look for country code based on administrative address. Return two
# digit country code if can do it; otherwise, return nil.
def admin_address(domain,message)
  # If no message at all, no whois, so give up
  if message == nil
    return nil
  end

  # The "i" at the end makes it case insensitive
  admin_country_row = message.split("\n").grep(/admin/i).grep(/country code/i)

  # I've seen records where the admin country row appears more than
  # once, for no good reason. If it does, just take the first one.
  if admin_country_row.count >= 1
    fields = admin_country_row[0].split(/:/)
    if fields.count == 1
      return nil
    else
      return "parsed\t" + resolve_country(domain,fields[1].strip())
    end

  else

    # "code" not explicity stated, key on "country" instead
    #admin_country_row = message.split("\n").grep(/admin/i).grep(/country/i)
    admin_country_row = message.split("\n").grep(/admin country/i)
    
    # I've seen records where the admin country row appears more than
    # once, for no good reason. If it does, just take the first one.
    if admin_country_row.count >= 1
      # The trailing negative means to keep null fields, i.e. if country is missing
      fields = admin_country_row[0].split(/:/,-1)
      return "parsed\t" + resolve_country(domain,fields[1].strip())

    else

      # Could not find a country code at all
      return nil
    end


  end

end


# For a .de address, pull the tech country code
def de_address(domain,message)

  if message==nil
    return nil
  end

  # First, verify that it looks like I think it should, where tech
  # address comes up first, then zone
  tech_location = message.index('[Tech-C]')
  zone_location = message.index('[Zone-C]')

  # If message doesn't contain any of the apporpriate text, all bets are off
  if tech_location==nil and zone_location==nil
    return nil
  end

  if !tech_location or !zone_location or tech_location >= zone_location
    puts "Domain: " + domain
    puts "Tech location: " + (tech_location || "")
    puts "Zone location: " + (zone_location || "")
    raise "de format not as expected "
  end

  # Now that we know tech location comes up first: grab first line in
  # the file containing CountryCode, and make sure it sits between
  # those two locations
  country_code_location = message.index("CountryCode")
  if country_code_location == nil or country_code_location < tech_location \
    or country_code_location > zone_location
    puts "Domain: " + domain
    puts "Tech location: " + (tech_location || "")
    puts "Zone location: " + (zone_location || "")
    puts "CountryCode location: " + (country_code_location || "")
    raise "de format not as expected on CountryCode"
  end

  # The "i" at the end makes it case insensitive
  country_code_row = message.split("\n").grep(/CountryCode/i)
  if country_code_row.count <= 1
    puts "Domain: " + domain
    raise "Couldn't find CountryCode row"
  end

  # Take first CountryCode row
  fields = country_code_row[0].split(/:/)
  if fields.count == 1
    return nil
  else
    return "de_parsed\t" + resolve_country(domain,fields[1].strip())
  end

end




# Look up alternative address based on GeoNames data
def alternative_address(domain,message)

  if message==nil
    return nil
  end

  # Try each alternative name available; if any appear in the message,
  # Speed updates from
  # http://stackoverflow.com/questions/11887145/fastest-way-to-check-if-a-string-matches-or-not-a-regexp-in-ruby
  match_counts = Hash.new(0)
  lower_message = message.downcase()
  # $alternatives.keys.each do |name|
  #  regexp = Regexp.new("[^[[:word:]]]" + name + "[^[[:word]]]").freeze    

  $alts_regex.keys.each do |ccode|

    regexp = $alts_regex[ccode]

    if  regexp =~ lower_message
      #match_counts[resolve_country(domain,$alternatives[name])]+=1
      match_counts[resolve_country(domain,ccode)]+=1
    end
  end

  # Shilad just wants a count for each country, so just turn it into a readable string
  if match_counts.keys.length == 0
    return nil
  else
    results = "geonames\t"
    match_counts.keys.each do |ccode|
      results += ccode + "|" + match_counts[ccode].to_s + "\t"
    end
    
    return results.strip()
  end
end



require 'pg'
require 'whois'
conn = PGconn.open(:dbname => 'whois')

res = conn.exec("select domain,message from domains order by domains");
res.each { |row|

  domain = row["domain"]
  message = row["message"]
    
  country = admin_address(domain,message) 
  if country==nil and domain[-3,3] == ".de"
    country = de_address(domain,message)
  end

  if country==nil
    country = alternative_address(domain,message)
  else
    country = country + "|1"
  end

  if country
    puts domain + "\t" + country
  else
    puts domain + "\t??"
  end

      
}
