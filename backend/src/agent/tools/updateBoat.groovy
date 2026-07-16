#!/usr/bin/env groovy
import groovy.util.XmlParser
import groovy.xml.XmlUtil
import groovy.util.CliBuilder

def cli = new CliBuilder(usage: 'updateBoat.groovy --xml FILE --id ID [options]')
cli.with {
    xml longOpt: 'xml', args: 1, required: true, 'Path to XML file'
    id longOpt: 'id', args: 1, required: true, 'Boat id to update'
    idNew longOpt: 'idNew', args: 1, 'New boat id (to change the boat id)'

    name longOpt: 'name', args: 1, 'Boat name'
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

// locate boats container
def boatsNode = (root.'boats' && root.'boats'.size()>0) ? root.'boats'[0] : null
if (!boatsNode) {
    System.err.println("<boats> container not found in XML")
    System.exit(3)
}

// find boat by id
def target = boatsNode.'boat'.find { it.@id == opts.id }
if (!target) {
    System.err.println("Boat with id ${opts.id} not found")
    System.exit(4)
}

// handle id change if requested
def newId = opts.idNew
if (newId != null && newId != false) {
    newId = newId.toString().trim()
    if (newId.length() > 0 && newId != opts.id) {
        // ensure no other boat already has this id
        def existing = boatsNode.'boat'.find { it.@id == newId }
        if (existing && existing != target) {
            System.err.println("Another boat already has id ${newId}")
            System.exit(5)
        }
        // update attribute
        target.@id = newId
    }
}

// helpers
def ensureNode = { parent, tag ->
    def c = parent."${tag}"
    if (c && c.size()>0) return c[0]
    return parent.appendNode(tag)
}

def setText = { parent, tag, text ->
    // If option not provided, CliBuilder may set it to null or false — ignore both
    if (text == null || text == false) return
    def str = text.toString()
    if (str.length() == 0) return
    def c = parent."${tag}"
    if (c && c.size()>0) {
        c[0].value = [str]
    } else {
        parent.appendNode(tag, str)
    }
}

// top-level fields
setText(target, 'name', opts.name)
setText(target, 'type', opts.type)
setText(target, 'lengthMeters', opts.length)
setText(target, 'beamMeters', opts.beam)
setText(target, 'draftMeters', opts.draft)
setText(target, 'yearBuilt', opts.year)
setText(target, 'homePort', opts.homePort)
setText(target, 'registrationNumber', opts.regNumber)

// owner
def ownerNode = ensureNode(target, 'owner')
setText(ownerNode, 'firstName', opts.ownerFirst)
setText(ownerNode, 'lastName', opts.ownerLast)
setText(ownerNode, 'contactPhone', opts.ownerPhone)
setText(ownerNode, 'email', opts.ownerEmail)

// engine
def engineNode = ensureNode(target, 'engine')
setText(engineNode, 'manufacturer', opts.engManu)
setText(engineNode, 'model', opts.engModel)
setText(engineNode, 'horsepower', opts.horsepower)
setText(engineNode, 'fuelType', opts.fuel)

// sails
def sailsNode = ensureNode(target, 'sails')
setText(sailsNode, 'main', opts.sailMain)
setText(sailsNode, 'jib', opts.sailJib)
setText(sailsNode, 'spinnaker', opts.sailSpin)

// equipment
def equipNode = ensureNode(target, 'equipment')
setText(equipNode, 'gps', opts.gps)
setText(equipNode, 'radar', opts.radar)
setText(equipNode, 'radio', opts.radio)

// write back
def serialized = XmlUtil.serialize(root)
xmlFile.withWriter('UTF-8') { w -> w << serialized }

def printedId = (newId && newId.length()>0) ? newId : opts.id
println "Updated boat ${printedId} in ${xmlFile.absolutePath}"
