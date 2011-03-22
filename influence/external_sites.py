from django.utils.functional import curry
import base64, urllib, urllib2
import json
from datetime import datetime, timedelta
from django.utils.datastructures import SortedDict

# contribution links
def _get_crp_url(type, standardized_name, ids, cycle=None):
    if type == 'industry':
        if "urn:crp:industry" not in ids:
            return None
        return "http://www.opensecrets.org/industries/indus.php?ind=%s" % ids['urn:crp:industry']
    elif (type == 'politician' and 'urn:crp:recipient' in ids) or type != 'politician':
        return "http://www.opensecrets.org/usearch/index.php?q=%s" % standardized_name
    return None

def _get_nimsp_url(type, standardized_name, ids, cycle):
    if type == 'organization' and 'urn:nimsp:organization' in ids:
        if cycle:
            return "http://www.followthemoney.org/database/topcontributor.phtml?u=%(id)s&y=%(cycle)s" % dict(id=ids['urn:nimsp:organization'], cycle=cycle)
        else:
            return "http://www.followthemoney.org/database/topcontributor.phtml?u=%(id)s" % dict(id=ids['urn:nimsp:organization'])
    elif type == 'politician' and 'urn:nimsp:recipient' in ids:
        return "http://www.followthemoney.org/database/uniquecandidate.phtml?uc=%(id)s" % dict(id=ids['urn:nimsp:recipient'])
    elif type == 'industry':
        return 'http://www.followthemoney.org/database/IndustryTotals.phtml'
    return None

def _get_td_url(type, standardized_name, ids, cycle):
    if type == 'industry':
        if "urn:crp:industry" not in ids:
            return None
        query_string = "contributor_industry=%s" % ids['urn:crp:industry']
    else:
        keywords = {'individual': 'contributor_ft', 'organization': 'organization_ft', 'politician': 'recipient_ft'}
        query_string = "%s=%s" % (keywords[type], standardized_name)
    if cycle:
        query_string += "&cycle=%s" % cycle
    return "http://transparencydata.com/contributions/#%s" % base64.b64encode(query_string)

def get_contribution_links(type, standardized_name, namespaces_and_ids, cycle):
    """ Return a list of (label, url) pairs for an organization. """
    
    ids = dict([(item['namespace'], item['id']) for item in namespaces_and_ids])
    if cycle == '-1':
        cycle = None

    links = [
        dict(text='OpenSecrets.org', url=_get_crp_url(type, standardized_name, ids, cycle)),
        dict(text='FollowTheMoney.org', url=_get_nimsp_url(type, standardized_name, ids, cycle)),
        dict(text='TransparencyData.com', url=_get_td_url(type, standardized_name, ids, cycle)),
    ]
    
    links = filter(lambda link: link['url'] is not None, links)

    return links


# grants and contracts links
def get_gc_links(standardized_name, cycle):
    # TD
    td_keywords = {}
    if cycle != '-1':
        td_keywords['fiscal_year'] = "%s|%s" % (int(cycle) - 1, cycle)
    
    grant_keywords = td_keywords.copy()
    grant_keywords.update({'recipient_ft': standardized_name})
    
    contract_keywords = td_keywords.copy()
    contract_keywords.update({'vendor_name': standardized_name})
    
    links = [
        dict(text='Grants & Loans on TransparencyData.com', url="http://transparencydata.com/grants/#%s" % base64.b64encode(urllib.urlencode(grant_keywords))),
        dict(text='Contracts on TransparencyData.com', url="http://transparencydata.com/contracts/#%s" % base64.b64encode(urllib.urlencode(contract_keywords)))
    ]
    
    # USA Spending
    usa_keywords = {'RecipientNameText': [standardized_name]}
    if cycle != '-1':
        usa_keywords['FiscalYear'] = [str(int(cycle) - 1), cycle]
    links.append(
        dict(text='USASpending.gov', url="http://usaspending.gov/search?query=&formFields=%s" % base64.b64encode(urllib.quote(json.dumps(usa_keywords))))
    )
    
    return links
    

def get_lobbying_links(type, standardized_name, ids, cycle):
    links = []
    
    # Reporting's Lobbyist Registration Tracker
    if type in ('firm', 'client'):
        tracker_urls = filter(lambda s: s['namespace'] == 'urn:sunlight:lobbyist_registration_tracker_url', ids)
        if tracker_urls:
            links.append(
                dict(text='Lobbyist Registration Tracker', url="http://reporting.sunlightfoundation.com" + tracker_urls[0]['id'])
            )
    
    # TD
    td_types = {'firm': 'registrant_ft', 'lobbyist': 'lobbyist_ft', 'client': 'client_ft'}
    td_params = {}
    if cycle != '-1':
        td_params['year'] = "%s|%s" % (int(cycle) - 1, cycle)
    
    if type in td_types:
        td_params[td_types[type]] = standardized_name
        
        links.append(
            dict(text='TransparencyData.com', url="http://transparencydata.com/lobbying/#%s" % base64.b64encode(urllib.urlencode(td_params)))
        )
    
    # OpenSecrets
    os_types = {'firm': 'f', 'lobbyist': 'l', 'client': 'c'}
    if type == 'lobbyist':
        indiv_ids = filter(lambda s: s['namespace'] == 'urn:crp:individual', ids)
        if indiv_ids:
            os_params = {'lname': standardized_name, 'id': indiv_ids[0]['id']}
            if cycle != '-1':
                os_params['year'] = cycle
            links.append(
                dict(text='OpenSecrets.orgs', url="http://www.opensecrets.org/lobby/lobbyist.php?%s" % urllib.urlencode(os_params))
            )
    elif type == 'industry':
        industry_ids = filter(lambda s: s['namespace'] == 'urn:crp:industry', ids)
        if industry_ids:
            os_params = {'lname': industry_ids[0]['id']}
            td_params = {'industry': industry_ids[0]['id']}
            if cycle != '-1':
                os_params['year'] = cycle
                td_params['year'] = cycle
            links.append(
                dict(text='OpenSecrets.orgs', url="http://www.opensecrets.org/lobby/indusclient.php?%s" % urllib.urlencode(os_params))
            )
            links.append(
                dict(text='TransparencyData.com', url="http://transparencydata.com/lobbying/#%s" % base64.b64encode(urllib.urlencode(td_params)))
            )
    
    else:
        links.append(
            dict(text='OpenSecrets.org', url="http://www.opensecrets.org/lobby/lookup.php?%s" % urllib.urlencode({'type': os_types[type], 'lname': standardized_name}))
        )
    
    return links

def get_earmark_links(type, standardized_name, ids, cycle):
    links = []
    
    # TD
    td_types = {'organization': 'recipient', 'politician': 'member'}
    td_params = {}
    if cycle != '-1':
        td_params['year'] = "%s|%s" % (int(cycle) - 1, cycle)
    
    if type in td_types:
        td_params[td_types[type]] = standardized_name
        
        links.append(
            dict(text='TransparencyData.com', url="http://transparencydata.com/earmarks/#%s" % base64.b64encode(urllib.urlencode(td_params)))
        )
    
    # OpenSecrets
    politician_ids = filter(lambda s: s['namespace'] == 'urn:crp:recipient', ids)
    if politician_ids:
        os_params = {'cid': politician_ids[0]['id']}
        if cycle != '-1':
            os_params['year'] = cycle
        links.append(
            dict(text='OpenSecrets.org', url="http://www.opensecrets.org/politicians/earmarks.php?%s" % urllib.urlencode(os_params))
        )
    
    return links

def get_partytime_data(ids):
    politician_ids = filter(lambda s: s['namespace'] == 'urn:crp:recipient', ids)
    
    if not politician_ids:
        return {'past': [], 'upcoming': []}
      
    page = urllib2.urlopen("http://politicalpartytime.org/json/%s/" % politician_ids[0]['id'])
    records = json.loads(page.read())
    
    today = datetime.now()
    cutoff = today - timedelta(days=180)
    
    out = SortedDict()
    out['upcoming'] = [dict(date=datetime.strptime(record['fields']['start_date'], '%Y-%m-%d'), **record) for record in records if record['fields']['start_date'] >= today.strftime('%Y-%m-%d')][:3]
    out['past'] = [dict(date=datetime.strptime(record['fields']['start_date'], '%Y-%m-%d'), **record) for record in records if record['fields']['start_date'] < today.strftime('%Y-%m-%d') and record['fields']['start_date'] >= cutoff.strftime('%Y-%m-%d')][(-1 * (5 - len(out['upcoming']))):]
    
    return out

def get_lobbyist_tracker_data(ids):
    out = []
    tracker_urls = filter(lambda s: s['namespace'] == 'urn:sunlight:lobbyist_registration_tracker_url', ids)
    if tracker_urls:
        page = urllib2.urlopen("http://reporting.sunlightfoundation.com%s.json" % tracker_urls[0]['id'])
        records = json.loads(page.read())
        out = list(reversed(records['registrations']))[-5:]
    return out