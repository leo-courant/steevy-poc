#!/usr/bin/env groovy
import groovy.util.XmlParser
import groovy.xml.XmlUtil
import groovy.util.CliBuilder

def cli = new CliBuilder(usage: 'addBoat.groovy --xml FILE --id ID [options]')
cli.with {
    xml longOpt: 'xml', args: 1, required: true, 'Path to XML file'
    id longOpt: 'id', args: 1, required: true, 'Boat id (e.g. B209)'
    name longOpt: 'name', args: 1, required: true, 'Boat name'
    type longOpt: 'type', args: 1, 'Boat type'
    length longOpt: 'length', args: 1, 'Length in meters'
    beam longOpt: 'beam', args: 1, 'Beam in meters'
    draft longOpt: 'draft', args: 1, 'Draft in meters'
    year longOpt: 'year', args: 1, 'Year built'
    homePort longOpt: 'homePort', args: 1, 'Home port'
    regNumber longOpt: 'regNumber', args: 1, 'Registration number'

    ownerFirst longOpt: 'ownerFirst', args: 1, 'Owner first name'
    ownerLast longOpt: 'ownerLast', args: 1, 'Owner last name'
    ownerPhone longOpt: 'ownerPhone', args: 1, 'Owner phone'
    ownerEmail longOpt: 'ownerEmail', args: 1, 'Owner email'

    engManu longOpt: 'engManu', args: 1, 'Engine manufacturer'
    engModel longOpt: 'engModel', args: 1, 'Engine model'
    horsepower longOpt: 'horsepower', args: 1, 'Engine horsepower'
    fuel longOpt: 'fuel', args: 1, 'Fuel type'

    sailMain longOpt: 'sailMain', args: 1, 'Main sail id'
    sailJib longOpt: 'sailJib', args: 1, 'Jib sail id'
    sailSpin longOpt: 'sailSpin', args: 1, 'Spinnaker id'

    gps longOpt: 'gps', args: 1, 'GPS id'
    radar longOpt: 'radar', args: 1, 'Radar id'
    radio longOpt: 'radio', args: 1, 'Radio id'

    help(longOpt: 'help', 'Show usage')
}

def opts = cli.parse(args)
if (!opts) System.exit(1)
if (opts.help) { cli.usage(); System.exit(0) }

def xmlFile = new File(opts.xml)
if (!xmlFile.exists()) {
    System.err.println("XML file not found: ${opts.xml}")
    System.exit(2)
}

def parser = new XmlParser()
def root = parser.parse(xmlFile)
// Ensure there's a <boats> container to hold boat entries
def boatsNode = null
if (root.'boats' && root.'boats'.size() > 0) {
    boatsNode = root.'boats'[0]
} else {
    boatsNode = root.appendNode('boats')
}

// Build new boat node
def newBoat = new groovy.util.Node(null, 'boat')
newBoat.attributes()['id'] = opts.id
newBoat.appendNode('name', opts.name)
if (opts.type) newBoat.appendNode('type', opts.type)
if (opts.length) newBoat.appendNode('lengthMeters', opts.length)
if (opts.beam) newBoat.appendNode('beamMeters', opts.beam)
if (opts.draft) newBoat.appendNode('draftMeters', opts.draft)
if (opts.year) newBoat.appendNode('yearBuilt', opts.year)
if (opts.homePort) newBoat.appendNode('homePort', opts.homePort)
if (opts.regNumber) newBoat.appendNode('registrationNumber', opts.regNumber)

def owner = newBoat.appendNode('owner')
if (opts.ownerFirst) owner.appendNode('firstName', opts.ownerFirst)
if (opts.ownerLast) owner.appendNode('lastName', opts.ownerLast)
if (opts.ownerPhone) owner.appendNode('contactPhone', opts.ownerPhone)
if (opts.ownerEmail) owner.appendNode('email', opts.ownerEmail)

def engine = newBoat.appendNode('engine')
if (opts.engManu) engine.appendNode('manufacturer', opts.engManu)
if (opts.engModel) engine.appendNode('model', opts.engModel)
if (opts.horsepower) engine.appendNode('horsepower', opts.horsepower)
if (opts.fuel) engine.appendNode('fuelType', opts.fuel)

def sails = newBoat.appendNode('sails')
if (opts.sailMain) sails.appendNode('main', opts.sailMain)
if (opts.sailJib) sails.appendNode('jib', opts.sailJib)
if (opts.sailSpin) sails.appendNode('spinnaker', opts.sailSpin)

def equipment = newBoat.appendNode('equipment')
if (opts.gps) equipment.appendNode('gps', opts.gps)
if (opts.radar) equipment.appendNode('radar', opts.radar)
if (opts.radio) equipment.appendNode('radio', opts.radio)

// Append to the <boats> container and serialize back to file (preserve pretty formatting via XmlUtil)
boatsNode.append(newBoat)
def serialized = XmlUtil.serialize(root)
xmlFile.withWriter('UTF-8') { w -> w << serialized }

println "Added boat ${opts.id} to ${xmlFile.absolutePath}"
