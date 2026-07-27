#!/usr/bin/env groovy
import groovy.util.CliBuilder
import groovy.util.XmlParser
import groovy.xml.XmlUtil


def cli = new CliBuilder(usage: 'deleteBoat.groovy --xml FILE --id ID [--name NAME]')
cli.with {
    xml longOpt: 'xml', args: 1, required: true, 'Path to XML file'
    id longOpt: 'id', args: 1, required: true, 'Boat id to delete'
    name longOpt: 'name', args: 1, 'Boat name to verify before deletion'
    help(longOpt: 'help', 'Show usage')
}


def opts = cli.parse(args)
if (!opts) System.exit(1)
if (opts.help) {
    cli.usage()
    System.exit(0)
}


def xmlFile = new File(opts.xml)
if (!xmlFile.exists()) {
    System.err.println("XML file not found: ${opts.xml}")
    System.exit(2)
}


def root = new XmlParser().parse(xmlFile)
def boatsNode = (root.'boats' && root.'boats'.size() > 0) ? root.'boats'[0] : null
if (!boatsNode) {
    System.err.println('<boats> container not found in XML')
    System.exit(3)
}


def requestedName = opts.name == null || opts.name == false ? null : opts.name.toString()
def target = boatsNode.'boat'.find { boat ->
    if (boat.@id != opts.id) return false
    return requestedName == null || boat.'name'.text() == requestedName
}
if (!target) {
    if (requestedName == null) {
        System.err.println("Boat with id ${opts.id} not found")
    } else {
        System.err.println("Boat with id ${opts.id} and name ${requestedName} not found")
    }
    System.exit(4)
}

boatsNode.remove(target)
xmlFile.withWriter('UTF-8') { writer -> writer << XmlUtil.serialize(root) }

println "Deleted boat ${opts.id} from ${xmlFile.absolutePath}"
