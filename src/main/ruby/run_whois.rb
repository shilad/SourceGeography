#!/usr/bin/env ruby
#
# Install using: gem install pg whois

Encoding.default_internal = Encoding::UTF_8
Encoding.default_external = Encoding::UTF_8

require 'whois'
require 'pg'

conn = PG::Connection.open(:host => ARGV[0], :user => ARGV[1], :password => ARGV[2], :dbname => ARGV[3])

for i in 0 .. 750
    domain = ''
    conn.transaction do
      res = conn.exec_params('
                lock table domains in SHARE ROW EXCLUSIVE mode;
                UPDATE domains
                SET    started = \'now()\'
                WHERE  domain = (SELECT domain FROM domains WHERE started IS NULL LIMIT 1)
                RETURNING domain')
      domain = res.getvalue(0, 0)
    end
    begin
        z
        $stderr.puts "looking up #{domain}"
        r = Whois.whois(domain)
        sv = r.server.class.name.demodulize
        res = r.parts.map(&:body).join("\n\n" + ("=+" * 40) + "\n\n")
        conn.transaction do
          conn.exec_params('
              UPDATE domains
              SET completed = \'now()\', status = \'C\', server = $1, message = $2
              WHERE domain = $3
           ', [sv, res, domain])
        end
    rescue Exception => e
        $stderr.puts e
        conn.transaction do
          conn.exec_params('
              UPDATE domains
              SET completed = \'now()\', status = \'E\', error = $1
              WHERE domain = $2
           ', [e, domain])
        end
    end
    sleep(3)
end



